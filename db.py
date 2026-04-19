import aiosqlite, asyncio, time
from sqlite3 import IntegrityError
from config import RECORD_HP, REVIVE, REVIVE_PERIOD
__all__ = ('DB',)


class DB():

    def __init__(self, platform: str, db_object: aiosqlite.Connection):
        self.db = db_object
        self.platform = platform

    async def _init(self):
        '''init for await

        Returns:
            self (DB)
        '''
        await self.db.execute(f'''CREATE TABLE IF NOT EXISTS {self.platform}_a_record_table(
                        a_record TEXT PRIMARY KEY,
                        time_dianxin NUMERIC DEFAULT (date('now')),
                        time_liantong NUMERIC DEFAULT (date('now')),
                        time_yidong NUMERIC DEFAULT (date('now')),
                        hp_dianxin TINYINT DEFAULT {RECORD_HP} CHECK(hp_dianxin <= {RECORD_HP}),
                        hp_liantong TINYINT DEFAULT {RECORD_HP} CHECK(hp_liantong <= {RECORD_HP}),
                        hp_yidong TINYINT DEFAULT {RECORD_HP} CHECK(hp_yidong <= {RECORD_HP}),
                        revive_dianxin TINYINT DEFAULT {REVIVE} CHECK(revive_dianxin <= {REVIVE}),
                        revive_liantong TINYINT DEFAULT {REVIVE} CHECK(revive_liantong <= {REVIVE}),
                        revive_yidong TINYINT DEFAULT {REVIVE} CHECK(revive_yidong <= {REVIVE}),
                        last_test_time_dianxin DATETIME DEFAULT (strftime('%s','now','-1 hour')),
                        last_test_time_liantong DATETIME DEFAULT (strftime('%s','now','-1 hour')),
                        last_test_time_yidong DATETIME DEFAULT (strftime('%s','now','-1 hour')))''')
        await self.db.commit()

        return self

    def __await__(self):
        return self._init().__await__()

    async def __aenter__(self) -> 'DB':
        return await self._init()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def insert(self, a_record: str):
        '''insert A record

        Args:
            a_record: a_record

        Returns:
            false: if exist the a_record to be insert
            true: if not exist
        '''
        try:
            await self.db.execute(
                f'INSERT INTO {self.platform}_a_record_table(a_record) VALUES(?)',
                (a_record,)
            )
        except IntegrityError:
            return False
        except Exception as e:
            print(e)
        else:
            await self.db.commit()
            return True

    async def down_record(self, isp: str, a_record: str):
        '''set A record down (hp_{isp} -= 1, revive_{isp} = 0, last_test_time_{isp} =  strftime('%s','now'))
        '''
        try:
            await self.db.execute(
                f'UPDATE {self.platform}_a_record_table SET hp_{isp} = hp_{isp} - 1, revive_{isp} = 0, last_test_time_{isp} = strftime("%s","now") WHERE a_record = ?',
                (a_record,)
            )
            await self.db.commit()
        except IntegrityError:
            pass
        except Exception as e:
            print(e)

    async def just_refresh_last_test_time(self, isp: str, a_record: str):
        '''just refresh last test time (set last_test_time_{isp} =  strftime('%s','now'))
        '''
        try:
            await self.db.execute(
                f'UPDATE {self.platform}_a_record_table SET last_test_time_{isp} = strftime("%s","now") WHERE a_record = ?',
                (a_record,)
            )
            await self.db.commit()
        except IntegrityError:
            pass
        except Exception as e:
            print(e)

    async def revive_add(self, isp: str, a_record: str):
        '''revive A record

        make revive_{isp} += 1

        Returns:
            REVIVE. return revive_{isp} when revive_{isp} < REVIVE
        '''
        try:
            await self.db.execute(
                f'UPDATE {self.platform}_a_record_table SET revive_{isp} = revive_{isp} + 1, last_test_time_{isp} = strftime("%s","now") WHERE a_record = ?',
                (a_record,)
            )
            await self.db.commit()
            res = await self._execute_select(
                f'SELECT revive_{isp} FROM {self.platform}_a_record_table WHERE a_record = ?',
                (a_record,)
            )
            return res[0][0]
        except IntegrityError:
            return REVIVE
        except Exception as e:
            print(e)
            return None

    async def revive_all(self, isp: str, a_record: str):
        '''revive all args of A record (hp_{isp} = {RECORD_HP}, time_{isp} = (date('now')))'''
        try:
            await self.db.execute(
                f'UPDATE {self.platform}_a_record_table SET hp_{isp} = {RECORD_HP}, time_{isp} = (date("now")), last_test_time_{isp} = strftime("%s","now") WHERE a_record = ?',
                (a_record,)
            )
            await self.db.commit()
        except Exception:
            pass

    async def _execute_select(self, sqlscript: str, params=None):
        '''

        Returns:
            list of (res,)
        '''
        cursor = await self.db.execute(sqlscript, params if params else ())
        res = await cursor.fetchall()
        await cursor.close()
        return res

    async def get_all_record(self):
        '''
        Returns:
            list of a_record
        '''
        res = []
        cursor = await self.db.execute(
            f'SELECT a_record FROM {self.platform}_a_record_table'
        )
        async for record in cursor:
            res.append(record[0])
        return res

    async def get_now_up_record(self, isp: str, limit: int = 10, offset: int = 0):
        '''select lines of now-up A record (revive_{isp} >= {REVIVE}, strftime('%s','now') - last_test_time_{isp} >= 60*15)

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,)
        '''
        return await self._execute_select(
            f'SELECT a_record FROM {self.platform}_a_record_table WHERE (revive_{isp} >= {REVIVE} AND strftime("%s","now") - last_test_time_{isp} >= 60*15) LIMIT ? OFFSET ?',
            (limit, offset * limit)
        )

    async def get_now_down_but_alive_record(self, isp: str, limit: int = 10, offset: int = 0):
        '''select lines of down record (revive_{isp} < {REVIVE}, strftime('%s','now') - last_test_time_{isp} >= 60*15) but still alive, which means its hp still greater than 0

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,)
        '''
        return await self._execute_select(
            f'SELECT a_record FROM {self.platform}_a_record_table WHERE (revive_{isp} < {REVIVE} AND hp_{isp} > 0 AND strftime("%s","now") - last_test_time_{isp} >= 60*15) LIMIT ? OFFSET ?',
            (limit, offset * limit)
        )

    async def get_about_to_revive_record(self, isp: str, limit: int = 10, offset: int = 0):
        '''lines of down record has been more than {REVIVE_PERIOD} days since the last revival

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,)
        '''
        return await self._execute_select(
            f'SELECT a_record FROM {self.platform}_a_record_table WHERE (julianday("now") - julianday(time_{isp}) >= {REVIVE_PERIOD}) LIMIT ? OFFSET ?',
            (limit, offset * limit)
        )

    async def close(self):
        await self.db.close()


if __name__ == '__main__':
    # for test
    async def main():
        start_time = time.time()
        async with aiosqlite.connect('sqlite_db.db') as db:
            async with DB('Vercel', db) as a:
                print(await a.get_now_up_record('dianxin', offset=2))
                print(await a.get_now_down_but_alive_record('yidong', offset=2))
                print(await a.get_about_to_revive_record('liantong'))
                print(await a.down_record('liantong', '1.1.1.3'))
                print(await a.revive_add('liantong', '1.1.1.6'))
                await a.revive_all('yidong', '1.1.1.8')
                print(await a.get_all_record())
                await a.just_refresh_last_test_time('dianxin', '76.76.21.22')
            print(time.time() - start_time)
    asyncio.run(main())

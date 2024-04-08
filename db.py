import aiosqlite,asyncio,time
from sqlite3 import IntegrityError
from config import RECORD_HP,REVIVE,REVIVE_PERIOD
__all__ = ('DB',)
class DB():

    def __init__(self, platform:str, db_object:aiosqlite.Connection) :
        self.db = db_object
        self.platform = platform
    async def _init(self):
        '''init for await

        Returns:
            self (DB)
        '''        
        
        await self.db.execute(f'''create table if not exists {self.platform}_a_record_table(
                        a_record text PRIMARY KEY,
                        time_dianxin numeric default (date('now')),
                        time_liantong numeric default (date('now')),
                        time_yidong numeric default (date('now')),
                        hp_dianxin tinyint default {RECORD_HP} check(hp_dianxin <= {RECORD_HP}),
                        hp_liantong tinyint default {RECORD_HP} check(hp_liantong <= {RECORD_HP}),
                        hp_yidong tinyint default {RECORD_HP} check(hp_yidong <= {RECORD_HP}),
                        revive_dianxin tinyint default {REVIVE} check(revive_dianxin <= {REVIVE}),
                        revive_liantong tinyint default {REVIVE} check(revive_liantong <= {REVIVE}),
                        revive_yidong tinyint default {REVIVE} check(revive_yidong <= {REVIVE}),
                        last_test_time_dianxin datetime default (strftime('%s','now','-1 hour')),
                        last_test_time_liantong datetime default (strftime('%s','now','-1 hour')),
                        last_test_time_yidong datetime default (strftime('%s','now','-1 hour')))''')
        await self.db.commit()
        
        return self
    def __await__(self):
        return self._init().__await__()    
    
    async def __aenter__(self) -> 'DB':
        return await self._init()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    
    async def insert(self,a_record:str):
        '''insert A record

        Args:
            a_record: a_record

        Returns:
            false: if exist the a_record to be insert
            true: if not exist
        '''        ''''''
        try:
            await self.db.execute(f'''insert into {self.platform}_a_record_table(a_record) values(\'{a_record}\')''')
        except IntegrityError:
            return False
        except Exception as e:
            print(e)
        else:
            await self.db.commit()
            return True
    async def down_record(self,isp:str,a_record:str):
        '''set A record down (hp_{isp} -= 1, revive_{isp} = 0, last_test_time_{isp} =  strftime('%s','now'))
        
        '''
        try:
            await self.db.execute(f'''update {self.platform}_a_record_table set hp_{isp} = hp_{isp} - 1, revive_{isp} = 0, last_test_time_{isp} =  strftime('%s','now') where a_record = \'{a_record}\'''')
            await self.db.commit()
        except IntegrityError:
            pass
        except Exception as e:
            print(e)
    async def just_refresh_last_test_time(self,isp:str,a_record:str):
        '''just refresh last test time (set last_test_time_{isp} =  strftime('%s','now'))
        '''   
        try:
            await self.db.execute(f'''update {self.platform}_a_record_table set last_test_time_{isp} =  strftime('%s','now') where a_record = \'{a_record}\'''')
            await self.db.commit()
        except IntegrityError:
            pass
        except Exception as e:
            print(e)
    async def revive_add(self, isp:str,a_record:str):
        '''revive A record

        make revive_{isp} += 1

        Returns:
            REVIVE. return revive_{isp} when revive_{isp} < REVIVE
        '''        
        try:
            await self.db.execute(f'''update {self.platform}_a_record_table 
                                  set revive_{isp} = revive_{isp} + 1, last_test_time_{isp} =  strftime('%s','now') 
                                  where a_record = \'{a_record}\'''')
            await self.db.commit()
            res  = await self._execute_select(f'''select revive_{isp} from {self.platform}_a_record_table where a_record = \'{a_record}\'''')
            return res[0][0]
        except IntegrityError:
            return REVIVE
        except Exception as e:
            print(e)
            return None
            

    async def revive_all(self,isp:str,a_record:str):
        '''revive all args of A record (hp_{isp} = {RECORD_HP}, time_{isp} = (date('now'))'''
        try:
            await self.db.execute(f'''update {self.platform}_a_record_table set hp_{isp} = {RECORD_HP},  time_{isp} = (date('now')), last_test_time_{isp} =  strftime('%s','now') where a_record = \'{a_record}\'''')
            await self.db.commit()
        except:
            pass
    async def _execute_select(self,sqlscript:str):
        '''

        Returns:
            list of (res,)
        '''
        cursor = await self.db.execute(sqlscript)
        res = await cursor.fetchall()
        await cursor.close()
        return res
    async def get_all_record(self):
        '''
        Returns:
            list of a_record
        '''        
        res = []
        cursor = await self.db.execute(f'''select a_record from {self.platform}_a_record_table''')
        async for record in cursor:
            res.append(record[0])
        return res
    async def get_now_up_record(self, isp:str, limit:int = 10, offset:int = 0):
        '''select lines of now-up A record (revive_{isp} >= {REVIVE}, strftime('%s','now') - last_test_time_{isp} >= 60*15)

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,)
        '''        
        
        return await self._execute_select(f'''select a_record from {self.platform}_a_record_table 
                                          where (revive_{isp} >= {REVIVE} and strftime('%s','now') - last_test_time_{isp} >= 60*15) 
                                          limit {limit} offset {offset * limit}''')
    
    async def get_now_down_but_alive_record(self, isp:str, limit:int = 10, offset:int = 0):
        '''select lines of down record (revive_{isp} < {REVIVE}, strftime('%s','now') - last_test_time_{isp} >= 60*15) but still alive, which means its hp still greater than 0

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,) 
        '''  
        return await self._execute_select(f'''select a_record from {self.platform}_a_record_table 
                                          where (revive_{isp} < {REVIVE} and hp_{isp} > 0 and strftime('%s','now') - last_test_time_{isp} >= 60*15 ) 
                                          limit {limit} offset {offset * limit}''')
    
    async def get_about_to_revive_record(self, isp:str, limit:int = 10, offset:int = 0):
        '''lines of down record has been more than {REVIVE_PERIOD} days since the last revival

        Args:
            isp: isp
            limit: defind limit clause in 'LIMIT n OFFSET m' sqlscript, of which n is equal to {limit}
            offset: defind offset clause in 'LIMIT n OFFSET m' sqlscript, of which m is equal to {offset} * {limit}. Defaults to 0.

        Returns:
            list of (a_record,)
        '''  
        
        return await self._execute_select(f'''select a_record from {self.platform}_a_record_table 
                                       where (julianday('now') - julianday(time_{isp}) >= {REVIVE_PERIOD} ) limit {limit} offset {offset * limit}''')
    async def close(self):
        # await self.db.close()
        pass
if __name__ == '__main__':
    # for test
    async def main():
        start_time = time.time()
        async with aiosqlite.connect('sqlite_db.db') as db:
            async with DB('Vercel',db) as a:
                # async with asyncio.TaskGroup() as tg:
                #     for i in range(10):
                #         tg.create_task(a.insert(f'1.1.1.{i}'))
                print(await a.get_now_up_record('dianxin',offset=2))
                print(await a.get_now_down_but_alive_record('yidong',offset=2))
                print(await a.get_about_to_revive_record('liantong'))
                print(await a.down_record('liantong','1.1.1.3'))
                print(await a.revive_add('liantong','1.1.1.6'))
                await a.revive_all('yidong','1.1.1.8')
                print(await a.get_all_record())
                await a.just_refresh_last_test_time('dianxin','76.76.21.22')
            print(time.time() - start_time)
    asyncio.run(main())
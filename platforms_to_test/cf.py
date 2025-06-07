
from aiosqlite import Connection
from .base_platform import Base_Platform
from config import CF_SELECTED_DOMAIN_LIST,CF_URL_TO_TEST
from crawler import *
import asyncio
__all__ = ('Cf',)


class Cf(Base_Platform):
    def __init__(self, db_object: Connection) -> None:
        super().__init__(db_object, 'Cf')
        self.CONCURRENCY = 2
        self.try_times = 4
    async def run_sub(self):
        if await self.db.get_all_record() == []:
            await self.refresh_dns()
    async def refresh_dns(self):
        cf_domain = self.domain_manager.get_next_selected_domain()
        res = await Crawler(session=self.session, url_to_test=cf_domain,test_type='dns').test()
        for a_record in res:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.insert_record(a_record))
if __name__ == '__main__':
   pass
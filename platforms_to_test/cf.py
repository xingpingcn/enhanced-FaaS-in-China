
from aiosqlite import Connection
from .base_platform import Base_Platform
from config import CF_SELECTED_DOMAIN_LIST
from crawler import *
import asyncio,random
__all__ = ('Cf',)
class Cf(Base_Platform):
    def __init__(self, db_object: Connection) -> None:
        super().__init__(db_object, 'Cf')
        self.CONCURRENCY = 3
    async def run_sub(self):
        if await self.db.get_all_record() == []:
            await self.refresh_dns()
    async def refresh_dns(self):
        cf_domain = random.choice(CF_SELECTED_DOMAIN_LIST)
        res = await Crawler(session=self.session, url_to_test=cf_domain,test_type='dns').test()
        for a_record in res:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.insert_record(a_record))
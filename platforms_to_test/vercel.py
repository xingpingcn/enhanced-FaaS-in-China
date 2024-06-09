from aiosqlite import Connection
from .base_platform import Base_Platform
import asyncio
__all__ = ('Vercel',)
class Vercel(Base_Platform):
    def __init__(self, db_object: Connection) -> None:
        super().__init__(db_object, 'Vercel')
    async def run_sub(self):
        if await self.db.get_all_record() == []:
            
            async with asyncio.TaskGroup() as main_tg:
                main_tg.create_task(self.refresh_dns())
                # vercel ip
                insert_list = ['34.95.57.145', '13.49.54.242', '18.178.194.147', '52.79.72.148', '35.180.16.12', '18.206.69.11', '52.76.85.65', '18.130.52.74', '35.202.100.12', '3.22.103.24',
                                '34.253.160.225', '18.229.231.184', '15.206.54.182', '35.235.101.253', '35.228.53.122',  '52.38.79.87', '13.238.105.1', '104.199.217.228', '18.162.37.140']
                for i in insert_list:
                    main_tg.create_task(self.insert_record(i))
            await self.refresh_dns()
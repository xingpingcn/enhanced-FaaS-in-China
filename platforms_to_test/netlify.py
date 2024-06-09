# from ..config import *
from aiosqlite import Connection
from .base_platform import Base_Platform
__all__ = ('Netlify',)
class Netlify(Base_Platform):
    def __init__(self, db_object: Connection) -> None:
        '''_summary_

        Args:
            db_object: db
        '''
        super().__init__(db_object,'Netlify') # same as class name
        
    async def run_sub(self):
        if await self.db.get_all_record() == []:
            await self.refresh_dns()
        
    
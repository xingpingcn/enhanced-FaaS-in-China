from .base_platform import Base_Platform
from config import VERCEL_TOKEN,BASE_DNS_URL_FOR_TEST,VERCEL_ADD_DOMAIN_PATH,VERCEL_BASE_API_URL
import asyncio
__all__ = ('Vercel',)
class Vercel(Base_Platform):
    async def update(self, ip_list:list):
        '''add domain to your project

        Args:
            ip_list: list of ip

        Return:
            None
        '''
        async with asyncio.TaskGroup() as tg:
            for ip in ip_list:
                tg.create_task(self.add(ip))
                               
    async def add(self, ip):
        headers = {
            "Authorization": f"Bearer {VERCEL_TOKEN}"
        }
        data = {
            "name":f'{ip}.{BASE_DNS_URL_FOR_TEST}'
        }
        async with self.session.post(VERCEL_BASE_API_URL+VERCEL_ADD_DOMAIN_PATH, json = data, headers = headers) as resp:
            return await resp.json()
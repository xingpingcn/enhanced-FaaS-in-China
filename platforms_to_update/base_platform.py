import aiohttp
__all__ = ('Base_Platform',)

class Base_Platform():
    def __init__(self,session) -> None:
   
        self.session:aiohttp.ClientSession = session
    async def _init(self):
        return self
    def __await__(self):
        return self._init().__await__()
    async def __aenter__(self):
        return await self._init()
    async def __aexit__(self,*a,**kw):
        pass
    async def update(self,ip_list,*a,**kw):
        '''Args:
            ip_list: list of ips, e.g. ["1.1.1.1"]. 
        Returns:
            status_code'''
        pass
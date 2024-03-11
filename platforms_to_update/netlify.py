# from ..config import *
from config import *
from .base_platform import Base_Platform
__all__ = ('Netlify',)
class Netlify(Base_Platform):
    async def update(self,ip_list: list | tuple | set = None, resq_type:str='update'):
        '''update alias to netlify

        Args:
            ip_list: list of ips, e.g. ["1.1.1.1"]. Defaults to None.
            resq_type: 'update' or 'get'. 'update' for change the aliases, 'get' for info.. Defaults to 'update'.

        Raises:
            AttributeError: when resq_type != 'update' or 'get'

        Returns:
            status_code
        '''

        header = {
            'Authorization': f'Bearer {NETLIFY_PAT}',
        }
        
        if resq_type == 'update':
            now_res = await self.update(resq_type='get')
            now_aliases_set = set(now_res["domain_aliases"])
            ip_set = {f'{ip}.{BASE_DNS_URL_FOR_TEST}' for ip in ip_list} | now_aliases_set
            data = {
            'domain_aliases': list(ip_set)
            }
            async with self.session.patch(BASE_NETLIFY_API_URL+UPDATE_NETLIFY_SITE_API_PATH, headers=header, json=data) as resp:
                return resp.status
        elif resq_type == 'get':
            async with self.session.get(BASE_NETLIFY_API_URL+UPDATE_NETLIFY_SITE_API_PATH, headers=header) as resp:
                return await resp.json()
        else:
            raise AttributeError('resq_type must be \'update\' or \'get\'')


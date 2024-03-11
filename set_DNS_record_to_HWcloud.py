import json
import asyncio
import aiohttp
import time
from config import *
__all__ = ('HWcloud',)


class HWcloud():
    def __init__(self, session: aiohttp.ClientSession) -> None:
        '''

        Example:
            >>> async with aiohttp.ClientSession() as session:
                    hwcloud = await HWcloud(session)
                    await hwcloud.update_batch_record_with_line(CNAME_BASE_URL['VERLIFY'], {'Netlify': {'dianxin': ['50.18.215.94']}})
        '''
        self.session = session
        self._token = ''
        self.headers = {}

        self.mapping_line_dict = {
            'dianxin': 'Dianxin',
            'liantong': 'Liantong',
            'yidong': 'Yidong',
            'default': 'default_view'
        }
        self.mapping_line_dict_reversed = {
            v: k for k, v in self.mapping_line_dict.items()}

    async def _init(self):
        try:
            json_file = open('HWcloud_token.json', 'rb')

        except:
            self._token = await self.refresh_token()
        else:
            json_dict = json.load(json_file)
            self._token, last_refresh_time = json_dict['token'], json_dict['last_refresh_time']
            if int(time.time()) - last_refresh_time >= 3600*6:
                self._token = await self.refresh_token()
            json_file.close()
        finally:

            json_dict = {
                'token': self._token,
                'last_refresh_time': int(time.time()),
            }
            with open('HWcloud_token.json', 'w') as f:
                json.dump(json_dict, f)
            self.headers = {
                'X-Auth-Token': self._token
            }
            return self

    def __await__(self):
        return self._init().__await__()

    @property
    def token(self):
        return self._token

    async def refresh_token(self):
        headers = {
            'Content-Type': 'application/json;charset=utf8'
        }
        data = {
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "domain": {
                                "name": f"{HW_IAM_DOMAIN}"  # IAM用户所属账号名
                            },
                            "name": f"{HW_IAM_USER}",  # IAM用户名
                            "password": f"{HW_IAM_PWD}"  # IAM用户密码
                        }
                    }
                },
                "scope": {
                    "project": {
                        "id": f"{HW_PROJECT_ID}"  # 项目id
                    }
                }
            }
        }

        async with self.session.post('https://iam.myhuaweicloud.com/v3/auth/tokens', json=data, headers=headers) as resq:
            return resq.headers['X-Subject-Token']

    async def add_one_record_to_HWcloud(self, ip: str):
        '''add record to HWcloud

        Args:
            ip: ip

        Returns:
            status
        '''
        url = f'{HW_HK_REGION_API_BASE_URL}{HW_ADD_ONE_RECORD_PATH}'

        data = {
            "name": f"{ip}.{BASE_DNS_URL_FOR_TEST}",
            "type": "A",
            "ttl": 3600,
            "records": [f"{ip}"],
        }
        async with self.session.post(url, json=data, headers=self.headers) as resp:
            return resp.status

    async def set_status(self, status: str, id: str):
        url = f'{HW_HK_REGION_API_BASE_URL}/v2.1/recordsets/{id}/statuses/set'
        data = {
            "status": status
        }
        async with self.session.put(url, json=data, headers=self.headers) as resp:
            await resp.json()

    async def create_sub_coro(self, data):
        url = f'{HW_HK_REGION_API_BASE_URL}{HW_CREATE_RECORD_WITH_BATCH_LINES_PATH}'
        async with self.session.post(url, json=data, headers=self.headers) as resp:
            # print(await resp.json())
            return await resp.json()

    async def create_cname_record_with_batch_lines(self, subdomain, answer_dict: dict):

        async with asyncio.TaskGroup() as tg:
            for platform, result_list in answer_dict.items():
                data = {
                    "name": f"{subdomain}",
                    "type": "A",
                    "description": platform,
                    "lines": [{
                            "line": self.mapping_line_dict[k],
                            "records": list(map(lambda x: x if not x == [] else [CNAME_DEFAULT_RECORD[platform.upper()]], [v]))[0],
                            "ttl": 300,
                            "weight": 1
                    } for k, v in result_list.items()]
                }
                tg.create_task(self.create_sub_coro(data))

    async def update_batch_record_with_line(self, subdomain: str, answer_dict: dict):
        '''update batch record with line to huawei cloud

        if there already exists the record to be update, this func will be call, otherwise self.create_cname_record_with_batch_lines will be call instead

        Args:
            subdomain: dns record domain. period must be add in the end due to huawei cloud limitation.
            answer_dict: dict containing list of dns answers classified by isp and platform

        Example:
            >>> await update_batch_record_with_line('test.domain.com.', {'Netlify':{"dianxin": ["54.253.236.92"], "liantong": ["54.253.236.1"], "yidong": ["54.253.236.2"]},'Vercel':{"dianxin": ["54.253.236.92"], "liantong": ["54.253.236.1"], "yidong": ["54.253.236.2"]}})
        '''

        async with self.session.get(f'{HW_HK_REGION_API_BASE_URL}/v2.1/recordsets?name={subdomain}', headers=self.headers) as resp:
            json_dict = await resp.json()
        id_list = json_dict['recordsets']
        if id_list == []:
            # if no record
            await self.create_cname_record_with_batch_lines(subdomain, answer_dict)
        else:
            # [ records, id, description] description must be equal to platform
            res_list = [[answer_dict[id_dict['description']][self.mapping_line_dict_reversed[id_dict['line']]],
                         id_dict['id'], id_dict['description']] for id_dict in id_list]
            async with asyncio.TaskGroup() as tg:
                for list_for_status in res_list:
                    if list_for_status[0] == []:
                        list_for_status[0] = [
                            CNAME_DEFAULT_RECORD[list_for_status[2].upper()]]
                        tg.create_task(self.set_status(
                            'DISABLE', list_for_status[1]))
                    else:
                        tg.create_task(self.set_status(
                            'ENABLE', list_for_status[1]))

            data = {
                'recordsets': [
                    {"id": info_list[1],
                     "ttl": 300,
                     "weight": 1,
                     "description": info_list[2],
                     "records":  info_list[0]} for info_list in res_list
                ]
            }
            async with self.session.put(f'{HW_HK_REGION_API_BASE_URL}{HW_UPDATE_BATCH_RECORD_WITH_LINES_PATH}', headers=self.headers, json=data) as resp:
                return await resp.json()


if __name__ == '__main__':
    async def main():
        async with aiohttp.ClientSession() as session:
            hwcloud = await HWcloud(session)
            print(await hwcloud.update_batch_record_with_line('test.domain.com.', {'Netlify': {"dianxin": [], "liantong": ["54.253.236.1"], "yidong": ["54.253.236.2"]}, 'Vercel': {"dianxin": ["54.253.236.92"], "liantong": ["54.253.236.1"], "yidong": ["54.253.236.2"]}}))

    asyncio.run(main())

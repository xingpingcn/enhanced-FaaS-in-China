from config import *
from crawler import *
from set_DNS_record_to_HWcloud import *
from platforms_to_update import *
import aiohttp
from aiosqlite import Connection
import asyncio
from db import *
import json
import time


class AccelerateInCN():
    def __init__(self, platform: str, db_object: Connection) -> None:
        self.platform = platform
        self.res_dict = {
            f'{self.platform}':
            {
                'result': {'dianxin': set(), 'liantong': set(), 'yidong': set()},
                'update_time': int(time.time())
            }
        }

        self.res_dict[f'{self.platform}']['result']['default'] = [
            CNAME_DEFAULT_RECORD[f'{self.platform}'.upper()]]
        self.res_backup = []
        self.db_object = db_object

    async def _init(self):
        self.db: DB = await DB(self.platform, self.db_object)
        # 并发控制 Concurrency control
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=7))
        self.hwcloud = await HWcloud(session=self.session)
        return self

    def __await__(self):
        return self._init.__await__()

    async def __aenter__(self):
        return await self._init()

    async def __aexit__(self, *a, **kw):
        await self.close()

    async def close(self):
        await self.db.close()
        await self.session.close()

    async def insert_record(self, ip: str, is_update=False):
        if await self.db.insert(ip) == True:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.hwcloud.add_one_record_to_HWcloud(ip))
                if is_update:
                    tg.create_task(globals()[self.platform]
                                   (self.session).update([ip]))
            print('waiting for dns resolution to take effect(20 minutes)')
            await asyncio.sleep(60*20)

    async def refresh_dns(self, minute=20):
        '''refresh dns

        Will be call if there is nothing in the db or all A records exist in the db become invalid. 

        Args:
            minute: minute to wait for dns resolution to take effect. Defaults to 10.
        '''
        dns_record_set = await Crawler(self.session, test_type='dns', url_to_test=globals()[f'{self.platform}_URL_TO_TEST'.upper()]).test()
        async with asyncio.TaskGroup() as tg:
            for a_record in dns_record_set:
                tg.create_task(self.insert_record(a_record))
            tg.create_task(globals()[self.platform](self.session).update(
                dns_record_set))
            print(
                f'waiting for dns resolution to take effect({minute} minutes)')
            await asyncio.sleep(60*minute)

    async def run(self):
        '''main enter

        Returns:
            result dict of ips classified by isp
            {f'{self.platform}':
            {
                'result': {'dianxin': [], 'liantong': [], 'yidong': []},
                'update_time': int(time.time())
            }}
        '''

        if await self.db.get_all_record() == []:
            await self.refresh_dns()
        if self.platform == 'Vercel':
            async with asyncio.TaskGroup() as main_tg:
                # vercel ip
                insert_list = ['34.95.57.145', '13.49.54.242', '18.178.194.147', '52.79.72.148', '35.180.16.12', '18.206.69.11', '52.76.85.65', '18.130.52.74', '35.202.100.12', '3.22.103.24',
                               '34.253.160.225', '18.229.231.184', '15.206.54.182', '35.235.101.253', '35.228.53.122',  '52.38.79.87', '13.238.105.1', '104.199.217.228', '18.162.37.140']

                for i in insert_list:
                    main_tg.create_task(self.insert_record(i, is_update=True))
        # wait for all dns records being set
        async with asyncio.TaskGroup() as main_tg:
            for isp in ['dianxin', 'yidong', 'liantong']:
                # for isp in ['dianxin']:
                main_tg.create_task(self.main(isp))
        for k, v in self.res_dict[self.platform]['result'].items():
            self.res_dict[self.platform]['result'][k] = list(
                self.res_dict[self.platform]['result'][k])
        for isp in ['dianxin', 'yidong', 'liantong']:
            length = len(self.res_dict[self.platform]['result'][isp])
            if length < FILTER_CONFIG[self.platform][isp]['a_record_count']:
                self.res_backup.sort(key=lambda x: (
                    x['un_code_200_count'], x['http_time']))
                self.res_dict[self.platform]['result'][isp].extend([res['ip'] for res in self.res_backup[0:min(
                    FILTER_CONFIG[self.platform][isp]['a_record_count']-length, len(self.res_backup))]])

        with open(f'{self.platform}.json', 'w') as f:
            json.dump(self.res_dict, f)
        print(self.res_dict)
        await self.hwcloud.update_batch_record_with_line(CNAME_BASE_URL[f'{self.platform}'.upper()], {self.platform: self.res_dict[self.platform]['result']})
        return self.res_dict

    async def test_and_filter(self, isp: str, now_up_record_list: list):
        for result in asyncio.as_completed(
                [Crawler(self.session, isp=[isp], url_to_test=f'https://{a_record[0]}.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}').test() for a_record in now_up_record_list if not a_record in self.res_dict[self.platform]['result'][isp]]):
            res = await result
            if res[isp]['error'] == False:
                res[isp]['speed'].sort()
                if res[isp]['un_code_200_count'] <= FILTER_CONFIG[self.platform][isp]['un_code_200_limit'] and res[isp]['speed'][int((99/100)*(res[isp]['code_200_count']+res[isp]['un_code_200_count']))-1] <= FILTER_CONFIG[self.platform][isp]['time_limit']:
                    # if != 200 <= FILTER_CONFIG[self.platform][self.platform][isp]['un_code_200_limit'] and p99 <= FILTER_CONFIG[self.platform][isp]['time_limit']:
                    if await self.db.revive_add(isp, res[isp]['url_to_test'].replace(f'.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}', '').replace('https://', '')) == REVIVE:
                        self.res_dict[f'{self.platform}']['result'][isp].add(
                            res[isp]['url_to_test'].replace(f'.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}', '').replace('https://', ''))
                else:
                    try:
                        time_limit_backup = FILTER_CONFIG[self.platform][isp]['time_limit_backup']
                        un_code_200_limit_backup = FILTER_CONFIG[self.platform][isp]['un_code_200_limit_backup']

                    except:
                        time_limit_backup = FILTER_CONFIG['defualt_time_limit_backup']
                        un_code_200_limit_backup = FILTER_CONFIG['defualt_un_code_200_limit_backup']

                    if res[isp]['un_code_200_count'] <= un_code_200_limit_backup and res[isp]['speed'][int((99/100)*(res[isp]['code_200_count']+res[isp]['un_code_200_count']))-1] <= time_limit_backup:
                        self.res_backup.append({
                            'ip': res[isp]['url_to_test'].replace(f'.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}', '').replace('https://', ''),
                            'http_time': res[isp]['speed'][int((99/100)*(res[isp]['code_200_count']+res[isp]['un_code_200_count']))-1],
                            'un_code_200_count': res[isp]['un_code_200_count']
                        })
                        await self.db.down_record(isp, res[isp]['url_to_test'].replace(f'.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}', '').replace('https://', ''))
                    else:
                        await self.db.down_record(isp, res[isp]['url_to_test'].replace(f'.{BASE_DNS_URL_FOR_TEST}{OPTIONAL_PATH}', '').replace('https://', ''))
                        print('eliminated', self.platform,
                              res[isp]["url_to_test"], res[isp]['speed'][-3:-1], res[isp]['speed'][0:3])

    async def main(self, isp):
        count_for_break = 0
        for _ in range(2):
            while 1:
                now_up_record_list = await self.db.get_now_up_record(isp)
                if not now_up_record_list == []:
                    await self.test_and_filter(isp, now_up_record_list)
                    if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                        count_for_break = 1
                        break
                else:
                    break
            while 1:
                if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                    count_for_break = 1
                    break
                now_down_but_alive_record_list = await self.db.get_now_down_but_alive_record(isp)
                if not now_down_but_alive_record_list == []:
                    await self.test_and_filter(isp, now_down_but_alive_record_list)
                else:
                    break

            while 1:
                if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                    count_for_break = 1
                    break
                about_to_revive_record = await self.db.get_about_to_revive_record(isp)
                if not about_to_revive_record == []:
                    async with asyncio.TaskGroup()as tg:
                        for record in about_to_revive_record:
                            tg.create_task(self.db.revive_all(isp, record[0]))
                    await self.test_and_filter(isp, about_to_revive_record)
                else:
                    break
            if count_for_break == 0:
                await self.refresh_dns()


if __name__ == '__main__':
    import aiosqlite

    async def main():
        async with aiosqlite.connect('sqlite_db.db') as db:
            async with AccelerateInCN('Vercel', db) as core:
                await core.run()

    asyncio.run(main())

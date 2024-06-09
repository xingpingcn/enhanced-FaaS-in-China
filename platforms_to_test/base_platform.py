
__all__ = ('Base_Platform',)



from config import *
from crawler import *
from set_DNS_record_to_HWcloud import *
from platforms_to_test import *
import aiohttp
from aiosqlite import Connection
import asyncio
from db import *
import json
import random,time


class Base_Platform():
    def __init__(self, db_object: Connection, platform) -> None:
        '''_summary_

        Args:
            db_object: db
            platform: platform. same as sub class name
        '''
        self.platform = platform
        self.res_dict = {
            f'{self.platform}':{
                'result': {'dianxin': set(), 'liantong': set(), 'yidong': set()},
                'update_time': int(time.time())
            }
        }

        self.res_dict[f'{self.platform}']['result']['default'] = [
            CNAME_DEFAULT_RECORD[f'{self.platform}'.upper()]]
        self.res_backup = {'dianxin': [], 'liantong': [], 'yidong': []}
        self.db_object = db_object
        self.CONCURRENCY = CONCURRENCY

    async def _init(self):
        self.db: DB = await DB(self.platform, self.db_object)
        # 并发控制 Concurrency control
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=self.CONCURRENCY))
        self.hwcloud = await HWcloud(session=self.session)
        return self

    def __await__(self):
        return self._init().__await__()

    async def __aenter__(self):
        return await self._init()

    async def __aexit__(self, *a, **kw):
        await self.close()

    async def close(self):
        await self.db.close()
        await self.session.close()

    async def insert_record(self, ip: str):
        await self.db.insert(ip)
                

    async def refresh_dns(self):
        '''refresh dns

        Will be call if there is nothing in the db or all A records exist in the db become invalid. 

        '''
        url:str = random.choice(globals()[f'{self.platform}_URL_TO_TEST'.upper()])
    
        dns_record_set = await Crawler(self.session, test_type='dns', url_to_test=url).test()
        async with asyncio.TaskGroup() as tg:
            for a_record in dns_record_set:
                tg.create_task(self.insert_record(a_record))
            
            
            

    async def run_sub(self):
        pass
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

        
        await self.run_sub()
        # wait for all dns records being set
        async with asyncio.TaskGroup() as main_tg:
            for isp in ['dianxin', 'yidong', 'liantong']:
            # for isp in ['liantong']:
                main_tg.create_task(self.main(isp))
        for k, v in self.res_dict[self.platform]['result'].items():
            self.res_dict[self.platform]['result'][k] = list(v)
        for isp in ['dianxin', 'yidong', 'liantong']:
            length = len(self.res_dict[self.platform]['result'][isp])
            if length < FILTER_CONFIG[self.platform][isp]['a_record_count']:
                self.res_backup[isp].sort(key=lambda x: (
                    x['un_code_200_count'], x['http_time']))
                self.res_dict[self.platform]['result'][isp].extend([res['ip'] for res in self.res_backup[isp][0:min(
                    FILTER_CONFIG[self.platform][isp]['a_record_count']-length, len(self.res_backup))]])

        with open(f'{self.platform}.json', 'w') as f:
            json.dump(self.res_dict, f)
        print(self.res_dict)
        await self.hwcloud.update_batch_record_with_line(CNAME_BASE_URL[f'{self.platform}'.upper()], {self.platform: self.res_dict[self.platform]['result']})
        return self.res_dict

    async def test_and_filter(self, isp: str, now_up_record_list: list):
        base_url = random.choice(globals()[self.platform.upper()+'_URL_TO_TEST'])
        
        for result in asyncio.as_completed(
                [Crawler(self.session, isp=[isp], url_to_test=base_url, force_resovle_ip=f'{a_record[0]}').test() for a_record in now_up_record_list if not a_record in self.res_dict[self.platform]['result'][isp]]):
            res = await result
            if res[isp]['error'] == False:
                res[isp]['speed'].sort()
                ip = res[isp]['test_ip']
                if res[isp]['un_code_200_count'] <= FILTER_CONFIG[self.platform][isp]['un_code_200_limit'] and res[isp]['speed'][int((99/100)*(res[isp]['code_200_count']+res[isp]['un_code_200_count']))-1] <= FILTER_CONFIG[self.platform][isp]['time_limit']:
                    # if != 200 <= FILTER_CONFIG[self.platform][self.platform][isp]['un_code_200_limit'] and p99 <= FILTER_CONFIG[self.platform][isp]['time_limit']:
                    if await self.db.revive_add(isp, ip) == REVIVE:
                        self.res_dict[f'{self.platform}']['result'][isp].add(ip)
                        print('hit', isp,self.platform,
                              ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3])
                else:
                    try:
                        time_limit_backup = FILTER_CONFIG[self.platform][isp]['time_limit_backup']
                        un_code_200_limit_backup = FILTER_CONFIG[self.platform][isp]['un_code_200_limit_backup']

                    except:
                        time_limit_backup = FILTER_CONFIG['defualt_time_limit_backup']
                        un_code_200_limit_backup = FILTER_CONFIG['defualt_un_code_200_limit_backup']

                    if res[isp]['un_code_200_count'] <= un_code_200_limit_backup and res[isp]['speed'][-1] <= time_limit_backup:
                        self.res_backup[isp].append({
                            'ip': ip,
                            'http_time': res[isp]['speed'][-1],
                            'un_code_200_count': res[isp]['un_code_200_count']
                        })
                        await self.db.just_refresh_last_test_time(isp, ip)
                        print('eliminated in stage2', isp,self.platform,
                              ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3])
                    else:
                        await self.db.down_record(isp, ip)
                        print('eliminated in stage3', isp,self.platform,
                              ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3],'un_code_200_count',res[isp]['un_code_200_count'],res[isp]['un_code_200_count'] <= un_code_200_limit_backup,
                              'time_limit_backup',time_limit_backup,res[isp]['speed'][-1] <= time_limit_backup,)

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
            if count_for_break == 0:
                await self.refresh_dns()
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
                if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count'] or self.res_backup[isp].__len__() >= RES_BACKUP_LENGTH:
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
            if not count_for_break == 0:
                break



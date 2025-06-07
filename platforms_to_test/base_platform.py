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
from upload_file_to_github import *
import random
class TestDomainManager:
    def __init__(self, url_to_test, selected_domain=[]):
        """初始化测试域名管理器
        
        Args:
            url_to_test: 测试域名列表
            selected_domain: 优选域名列表，默认为空列表
        """
        self._url_to_test = set(url_to_test)   # 使用集合存储测试域名
        self._selected_domain = set(selected_domain)   # 使用集合存储优选域名
        
        # 跟踪域名的使用状态和冷却时间
        self._domains_in_use = {}  # 存储正在使用的域名及其开始时间
        self._domains_cooling = {}  # 存储冷却中的域名及其冷却结束时间
        self._cooldown_period = 8  # 域名冷却时间（秒）
        
        # 添加两个事件分别用于通知测试域名和优选域名的可用状态
        self._test_domains_available_event = asyncio.Event()
        self._selected_domains_available_event = asyncio.Event()
        
        # 缓存当前可用域名，避免重复计算
        self._available_test_domains = list(self._url_to_test)
        self._available_selected_domains = list(self._selected_domain)
        self._last_available_check_time = 0
        self._cache_validity_period = 0.5  # 缓存有效期(秒)
        
        # 缓存状态标志 - 指示缓存是否需要更新
        self._cache_dirty = False
        
        # 初始设置事件状态
        if self._url_to_test:
            self._test_domains_available_event.set()
        if self._selected_domain:
            self._selected_domains_available_event.set()
    
    def _ensure_cache_updated(self):
        """确保缓存是最新的，如果需要则更新缓存"""
        current_time = time.time()
        
        # 如果缓存已标记为脏或超过有效期，则更新缓存
        if self._cache_dirty or current_time - self._last_available_check_time >= self._cache_validity_period:
            self._update_available_domains(current_time)
            self._cache_dirty = False
    
    def _update_available_domains(self, current_time=None):
        """更新可用域名缓存
        
        Args:
            current_time: 当前时间，如果为None则获取当前时间
        """
        if current_time is None:
            current_time = time.time()
        
        # 更新测试域名的可用列表
        self._available_test_domains = [
            d for d in self._url_to_test 
            if d not in self._domains_in_use and 
            (d not in self._domains_cooling or current_time > self._domains_cooling.get(d, 0))
        ]
        
        # 更新优选域名的可用列表
        self._available_selected_domains = [
            d for d in self._selected_domain 
            if d not in self._domains_in_use and 
            (d not in self._domains_cooling or current_time > self._domains_cooling.get(d, 0))
        ]
        
        # 更新缓存时间
        self._last_available_check_time = current_time
        
        # 更新事件状态
        if self._available_test_domains:
            self._test_domains_available_event.set()
        else:
            self._test_domains_available_event.clear()
            
        if self._available_selected_domains:
            self._selected_domains_available_event.set()
        else:
            self._selected_domains_available_event.clear()
    
    def get_next_url_to_test(self):
        """获取下一个可用的测试域名，如果所有域名都在使用中则返回None"""
        if not self._url_to_test:  # 如果没有域名，返回None
            return None
        
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果没有可用测试域名，返回None
        if not self._available_test_domains:
            return None
        
        # 随机选择一个可用测试域名
        domain = random.choice(self._available_test_domains)
        
        # 标记为使用中并从可用列表中移除
        self._domains_in_use[domain] = time.time()
        self._available_test_domains.remove(domain)
        
        # 如果已经没有可用测试域名，清除事件
        if not self._available_test_domains:
            self._test_domains_available_event.clear()
            
        return domain
    
    def get_next_selected_domain(self):
        """获取下一个可用的优选域名，如果所有优选域名都在使用中则返回None"""
        if not self._selected_domain:  # 如果没有优选域名，返回None
            return None
        
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果没有可用优选域名，返回None
        if not self._available_selected_domains:
            return None
        
        # 随机选择一个可用优选域名
        domain = random.choice(self._available_selected_domains)
        
        # 标记为使用中并从可用列表中移除
        self._domains_in_use[domain] = time.time()
        self._available_selected_domains.remove(domain)
        
        # 如果已经没有可用优选域名，清除事件
        if not self._available_selected_domains:
            self._selected_domains_available_event.clear()
            
        return domain
    
    async def wait_for_test_domain_available(self, timeout=None):
        """等待直到有测试域名可用
        
        Args:
            timeout: 等待超时时间(秒)，None表示无限等待
            
        Returns:
            True: 有测试域名变为可用
            False: 等待超时
        """
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果已有可用域名，直接返回
        if self._available_test_domains:
            return True
            
        try:
            await asyncio.wait_for(self._test_domains_available_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def wait_for_selected_domain_available(self, timeout=None):
        """等待直到有优选域名可用
        
        Args:
            timeout: 等待超时时间(秒)，None表示无限等待
            
        Returns:
            True: 有优选域名变为可用
            False: 等待超时
        """
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果已有可用域名，直接返回
        if self._available_selected_domains:
            return True
            
        try:
            await asyncio.wait_for(self._selected_domains_available_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    async def wait_for_any_domain_available(self, timeout=None):
        """等待直到有任何域名可用
        
        Args:
            timeout: 等待超时时间(秒)，None表示无限等待
            
        Returns:
            True: 有域名变为可用
            False: 等待超时
        """
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果已有可用域名，直接返回
        if self._available_test_domains or self._available_selected_domains:
            return True
            
        # 等待任一事件触发
        try:
            if timeout is None:
                # 无限等待任一事件触发
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(self._test_domains_available_event.wait()),
                        asyncio.create_task(self._selected_domains_available_event.wait())
                    ],
                    return_when=asyncio.FIRST_COMPLETED
                )
                # 取消未完成的任务
                for task in pending:
                    task.cancel()
                return True
            else:
                # 有超时限制的等待
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(self._test_domains_available_event.wait()),
                        asyncio.create_task(self._selected_domains_available_event.wait())
                    ],
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED
                )
                # 取消未完成的任务
                for task in pending:
                    task.cancel()
                return len(done) > 0
        except asyncio.TimeoutError:
            return False
    
    def mark_domain_completed(self, domain):
        """标记域名测试完成，进入冷却期
        
        Args:
            domain: 完成测试的域名
        """
        # 从使用中移除
        if domain in self._domains_in_use:
            del self._domains_in_use[domain]
            
        # 设置冷却期结束时间
        self._domains_cooling[domain] = time.time() + self._cooldown_period
        
        # 创建一个任务，在冷却期结束后设置事件
        asyncio.create_task(self._set_domain_available_after_cooldown(domain))
        
        # 标记缓存为脏，下次获取域名时会更新缓存
        self._cache_dirty = True
    
    async def _set_domain_available_after_cooldown(self, domain):
        """在冷却期结束后设置相应的事件
        
        Args:
            domain: 完成冷却的域名
        """
        # 等待冷却期结束
        cooldown_end_time = self._domains_cooling.get(domain, 0)
        current_time = time.time()
        
        if cooldown_end_time > current_time:
            await asyncio.sleep(cooldown_end_time - current_time)
        
        # 从冷却列表中移除
        if domain in self._domains_cooling:
            del self._domains_cooling[domain]
        
        # 标记缓存为脏，强制下次获取域名时更新缓存
        self._cache_dirty = True
        
        # 可能有域名变为可用，通过缓存更新来设置事件
        self._ensure_cache_updated()
    
    def is_all_domains_in_use(self):
        """检查是否所有域名都在使用中或冷却中"""
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 如果有可用域名，返回False，否则返回True
        return not (self._available_test_domains or self._available_selected_domains)
    
    def is_all_test_domains_in_use(self):
        """检查是否所有测试域名都在使用中或冷却中"""
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 返回是否没有可用测试域名
        return not self._available_test_domains
    
    def is_all_selected_domains_in_use(self):
        """检查是否所有优选域名都在使用中或冷却中"""
        # 确保缓存是最新的
        self._ensure_cache_updated()
        
        # 返回是否没有可用优选域名
        return not self._available_selected_domains
class Base_Platform():
    def __init__(self, db_object: Connection, platform) -> None:
        '''_summary_

        Args:
            db_object: db
            platform: platform. same as sub class name
        '''
        self.concurrency_interval = 2 # seconds. for concurrency control
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
        self.try_times = 2 # how many times it will try in main()
        self.db_object = db_object
        self.CONCURRENCY = CONCURRENCY
        
        # 为每个平台创建自己的域名管理器实例
        platform_url_to_test = globals().get(f'{platform.upper()}_URL_TO_TEST', [])
        platform_selected_domain = globals().get(f'{platform.upper()}_SELECTED_DOMAIN_LIST', globals().get(f'{platform.upper()}_URL_TO_TEST', []))
        self.domain_manager = TestDomainManager(platform_url_to_test, platform_selected_domain)

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
                

    async def refresh_dns(self, count_max=3):
        '''refresh dns

        Will be called if there is nothing in the db or all A records exist in the db become invalid.
        Uses TestDomainManager to get an available domain for testing.
        '''
        # Get an available test URL using the domain manager
        url = self.domain_manager.get_next_selected_domain()
        
        # If no URL is available, wait for one to become available
        count = 0
        while url is None:
            print(f"等待可用测试域名selected_domai...")
            await self.domain_manager.wait_for_selected_domain_available(timeout=30)
            url = self.domain_manager.get_next_selected_domain()
            count += 1
            if count > count_max:
                print("等待超时，所有测试域名都在使用中")
                return
            
        
        try:
            print(f"正在刷新DNS记录，使用域名: {url}")
            dns_record_set = await Crawler(self.session, test_type='dns', url_to_test=url).test()
            async with asyncio.TaskGroup() as tg:
                for a_record in dns_record_set:
                    tg.create_task(self.insert_record(a_record))
        except Exception as e:
            print(f"刷新DNS记录时发生错误: {e}")
            # 如果发生错误，标记域名为完成，以便在冷却期后再次使用
           
        finally:
            # Mark the domain as completed (available after cooldown)
            if url:
                self.domain_manager.mark_domain_completed(url)
            
            

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
        isps = ['dianxin', 'yidong', 'liantong']
        await self.main(isps)
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
        await upload_to_github(f'{self.platform}.json', self.session)
        return self.res_dict

    async def test_and_filter(self, isps: list, now_up_record_list: list[str]):
        """同时测试多个ISP的IP列表
        
        Args:
            isps: ISP列表，如 ['dianxin', 'yidong', 'liantong']
            now_up_record_list: IP记录列表
        """
        # 过滤出需要测试的记录
        to_test = []
        for a_record in now_up_record_list:
            if any(a_record not in self.res_dict[self.platform]['result'][isp] for isp in isps):
                to_test.append(a_record)
        
        if not to_test:
            return
        
        # 创建一个结果队列
        result_queue = asyncio.Queue()
        
        # 定义处理结果的异步函数
        async def process_result(res, test_url=''):
            # 处理结果，筛选出符合条件的IP
            for isp in isps:
                if isp in res and res[isp]['error'] == False:
                    res[isp]['speed'].sort()
                    ip = res[isp]['test_ip']
                    
                    # 检查IP是否满足主要筛选条件
                    if res[isp]['un_code_200_count'] <= FILTER_CONFIG[self.platform][isp]['un_code_200_limit'] and res[isp]['speed'][int((99/100)*(res[isp]['code_200_count']+res[isp]['un_code_200_count']))-1] <= FILTER_CONFIG[self.platform][isp]['time_limit']:
                        if await self.db.revive_add(isp, ip) == REVIVE:
                            self.res_dict[f'{self.platform}']['result'][isp].add(ip)
                            print('hit', isp, self.platform,
                                ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3])
                    else:
                        # 备用筛选条件
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
                            print('eliminated in stage2', isp, self.platform,
                                ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3])
                        else:
                            await self.db.down_record(isp, ip)
                            print('eliminated in stage3', isp, self.platform,
                                ip, res[isp]['speed'][-3:], res[isp]['speed'][0:3], 'un_code_200_count', res[isp]['un_code_200_count'], res[isp]['un_code_200_count'] <= un_code_200_limit_backup,
                                'time_limit_backup', time_limit_backup, 'url', res[isp]['url_to_test'], res[isp]['speed'][-1] <= time_limit_backup,)
            
            # 标记域名测试完成，允许它在冷却期后再次使用
            # if test_url:
            #     self.domain_manager.mark_domain_completed(test_url)
        
        # 定义结果处理器
        async def result_processor():
            while True:
                item = await result_queue.get()
                if item is None:  # None作为结束信号
                    break
                res, test_url = item
                await process_result(res, test_url)
                result_queue.task_done()
        
        # 启动结果处理器
        processor_task = asyncio.create_task(result_processor())
        
        # 上次任务启动时间
        last_start_time = 0
        
        # 处理每条记录
        for a_record in to_test:
            # 计算等待时间，确保间隔
            now = time.time()
            wait_time = max(0, last_start_time + self.concurrency_interval - now)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # 获取URL
            url_to_test = None
            times_count = 0
            while url_to_test is None and times_count < 3:
                # 先尝试从优选域名获取，再从普通测试域名获取
                url_to_test = self.domain_manager.get_next_url_to_test()
                
                # 如果没有可用域名，等待直到有域名变为可用
                if url_to_test is None:
                    # print(f"所有url_to_test域名都在使用中，等待域名变为可用... {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    await self.domain_manager.wait_for_test_domain_available(timeout=60)
                    times_count += 1
                    # 即使超时也继续尝试
            
            ip = a_record[0]
            print('get url to test:', url_to_test, 'for ISPs:', isps)
            
            # 创建并启动Crawler任务
            async def run_crawler(test_url, test_ip, test_isps):
                try:
                    result = await Crawler(
                        self.session, 
                        isp=test_isps,  # 传入多个ISP
                        url_to_test=test_url, 
                        force_resovle_ip=f'{test_ip}'
                    ).test()
                    self.domain_manager.mark_domain_completed(test_url)
                    if not result:
                        print(f"测试结果为空，可能是网络问题或其他原因")
                        return
                    # 将结果和测试用的URL一起放入队列
                    else:
                        await result_queue.put((result, test_url))
                    
                except Exception as e:
                    print(f"Crawler执行出错: {e}")
                    # 出错时也要标记域名完成，否则会导致域名无法再次使用
                    self.domain_manager.mark_domain_completed(test_url)
            
            # 启动测试任务，传入多个ISP
            asyncio.create_task(run_crawler(url_to_test, ip, isps))
            
            # 更新上次启动时间
            last_start_time = time.time()
        
        # 等待所有结果处理完成
        try:
            await asyncio.wait_for(result_queue.join(), timeout=120)  # 增加超时时间，因为要处理多个ISP
        except asyncio.TimeoutError:
            print("等待结果处理超时")
        
        # 发送结束信号并等待处理器完成
        await result_queue.put(None)
        await processor_task

    async def main(self, isps=None):
        """测试指定的ISP，可以是单个ISP或多个ISP
        
        Args:
            isps: 可以是单个ISP字符串或ISP列表，如果为None则默认为当前调用的单个ISP
        """
        # 确保isps是列表
        if isps is None:
            # 兼容当前调用方式
            print("警告：没有指定ISP，无法执行测试")
            return
        elif isinstance(isps, str):
            isps = [isps]  # 转换单个ISP为列表
        
        count_for_break = {isp: 0 for isp in isps}
        
        for _ in range(self.try_times):
            # 处理当前状态为UP的记录
            all_up_records = []
            need_refresh_dns = False
            
            for isp in isps:
                if count_for_break[isp] == 1:
                    continue
                    
                now_up_record_list = await self.db.get_now_up_record(isp)
                if now_up_record_list:
                    all_up_records.extend(now_up_record_list)
                else:
                    need_refresh_dns = True
            
            # 去除重复记录
            all_up_records = list({record[0]: record for record in all_up_records}.values())
            
            if all_up_records:
                # 同时测试所有ISP的记录
                await self.test_and_filter(isps, all_up_records)
                
                # 检查每个ISP是否已经达到目标记录数
                for isp in isps:
                    if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                        count_for_break[isp] = 1
            
            # 如果所有ISP都已达标，则退出循环
            if all(count_for_break.values()):
                break
                
            # 刷新DNS记录（如果需要）
            if need_refresh_dns:
                await self.refresh_dns()
            
            # 处理当前状态为DOWN但还活着的记录
            print('2', self.res_dict[f'{self.platform}']['result'])
            all_down_alive_records = []
            for isp in isps:
                if count_for_break[isp] == 1:
                    continue
                    
                if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                    count_for_break[isp] = 1
                    continue
                    
                now_down_but_alive_record_list = await self.db.get_now_down_but_alive_record(isp)
                if now_down_but_alive_record_list:
                    all_down_alive_records.extend(now_down_but_alive_record_list)
            
            # 去除重复记录
            all_down_alive_records = list({record[0]: record for record in all_down_alive_records}.values())
            
            if all_down_alive_records:
                # 同时测试所有ISP的记录
                await self.test_and_filter(isps, all_down_alive_records)
                
                # 检查每个ISP是否已经达到目标记录数
                for isp in isps:
                    if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                        count_for_break[isp] = 1
            
            # 如果所有ISP都已达标，则退出循环
            if all(count_for_break.values()):
                break
            
            # 处理即将复活的记录
            print('3', self.res_dict[f'{self.platform}']['result'])
            remaining_isps = [isp for isp in isps if count_for_break[isp] == 0 and 
                            self.res_dict[f'{self.platform}']['result'][isp].__len__() < FILTER_CONFIG[self.platform][isp]['a_record_count'] and 
                            self.res_backup[isp].__len__() < RES_BACKUP_LENGTH]
            
            if not remaining_isps:
                break  # 没有需要继续处理的ISP
            
            for isp in remaining_isps:
                about_to_revive_record = await self.db.get_about_to_revive_record(isp)
                if about_to_revive_record:
                    # 先将记录标记为已恢复
                    async with asyncio.TaskGroup() as tg:
                        for record in about_to_revive_record:
                            tg.create_task(self.db.revive_all(isp, record[0]))
                    
                    # 然后测试这些记录（只针对当前ISP）
                    await self.test_and_filter([isp], about_to_revive_record)
                    
                    # 检查是否已达标
                    if self.res_dict[f'{self.platform}']['result'][isp].__len__() >= FILTER_CONFIG[self.platform][isp]['a_record_count']:
                        count_for_break[isp] = 1

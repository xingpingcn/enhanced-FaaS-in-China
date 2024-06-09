import asyncio,aiosqlite,aiohttp
from platforms_to_test import *
from platforms_to_test import __all__
import set_DNS_record_to_HWcloud
from config import CNAME_BASE_URL

async def task(platform,db):

    async with globals()[f'{platform}'](db) as core:
        return await core.run()


async def main():
    async with aiosqlite.connect('./sqlite_db.db') as db:
        res = await asyncio.gather(*[task(platform,db) for platform in __all__])
        # res = await asyncio.gather(*[task(platform,db) for platform in ['Cf']])
        merge_dict = {}
        # for VERLIFY
        for result_dict in res:
            if not list(result_dict.keys())[0] == 'Cf':
                merge_dict.update(result_dict)
        res_dict = {k:v['result'] for k,v in merge_dict.items()}
        print(res_dict)
        async with aiohttp.ClientSession() as session:
            hwcloud = await set_DNS_record_to_HWcloud.HWcloud(session)
            await hwcloud.update_batch_record_with_line(CNAME_BASE_URL['VERLIFY'],res_dict)
asyncio.run(main())

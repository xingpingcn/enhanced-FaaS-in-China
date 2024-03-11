import core
import asyncio
import aiosqlite
import aiohttp
import platforms_to_update
import set_DNS_record_to_HWcloud
from config import CNAME_BASE_URL


async def task(platform, db):
    async with core.AccelerateInCN(platform, db) as core0:
        return await core0.run()


async def main():
    async with aiosqlite.connect('./sqlite_db.db') as db:
        res = await asyncio.gather(*[task(platform, db) for platform in platforms_to_update.__all__])
        merge_dict = {}
        for result_dict in res:
            merge_dict.update(result_dict)
        res_dict = {k: v['result'] for k, v in merge_dict.items()}
        async with aiohttp.ClientSession() as session:
            hwcloud = await set_DNS_record_to_HWcloud.HWcloud(session)
            await hwcloud.update_batch_record_with_line(CNAME_BASE_URL['VERLIFY'], res_dict)
asyncio.run(main())

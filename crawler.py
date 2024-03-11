import asyncio
import aiohttp


__all__ = ('Crawler',)


class Crawler():

    def __init__(self, session: aiohttp.ClientSession, isp:list = ['dianxin','liantong','yidong'], url_to_test: str = None, test_type: str = 'http') -> None:
        '''test url

        Args:
            session: session
            isp: list of isp. Defaults to ['dianxin','liantong','yidong']
            url_to_test: test url. Defaults to none.
            test_type: dns or http. Defaults to 'http'.

        Return:
            dict: {'url_to_test' : '','code_200_count': 0, 'un_code_200_count': 0, 'speed': [str]}
        Example:
            >>> Crawler(session, url_to_test = 'https://baidu.com', test_type= 'dns').test()
            >>> {'44.219.53.183', '46.137.195.11', '52.74.166.77', '50.18.215.94', '35.169.59.174', '13.251.96.10', '54.253.236.10', '3.70.101.28', '54.66.176.79', '13.215.144.61', '18.192.231.252', '52.67.97.86', '18.139.194.139', '35.156.224.161', '13.228.199.255', '52.58.254.253', '52.9.166.110', '54.232.109.9', '3.72.140.173'}

            >>> Crawler(session, url_to_test = 'https://baidu.com', test_type= 'http').test()
            >>> {'url_to_test': 'https://baidu.com', 'dianxin': {'code_200_count': 32, 'un_code_200_count': 0, 'speed': [225, 271, 270, 259, 303, 322, 328, 358, 358, 395, 254, 382, 441, 421, 407, 436, 447, 471, 492, 526, 327, 394, 227, 320, 329, 1888, 2382, 3284, 3174, 6224, 4435, 7833]}, 'liantong': {'code_200_count': 31, 'un_code_200_count': 0, 'speed': [152, 202, 204, 219, 217, 240, 255, 239, 234, 267, 259, 272, 278, 299, 293, 306, 316, 308, 316, 326, 240, 386, 346, 215, 261, 324, 220, 308, 307, 352, 495]}, 'yidong': {'code_200_count': 30, 'un_code_200_count': 1, 'speed': [194, 220, 264, 239, 291, 299, 331, 336, 375, 396, 352, 408, 351, 389, 442, 530, 302, 308, 399, 363, 320, 319, 392, 492, 334, 362, 262, 310, 332, 274, 0]}}
'''
        self.session = session
        self.isp = isp
        self.id_json = {}
        self.url_to_test = url_to_test
        self.test_type = test_type
        self.mapping_dict = {
            'dianxin':'电信',
            'liantong':'联通',
            'yidong':'移动'
        }
        self.mapping_dict_reversed = {v:k for k,v in self.mapping_dict.items()}


    async def test(self):
        '''test

        Returns:
            Iteratable Object of result. {'url_to_test' : '','code_200_count'[int]: 0, 'un_code_200_count'[int]: 0, 'speed'[int]: []}
        '''

        pass


if __name__ == '__main__':
    # for test

    async def main():
        async with aiohttp.ClientSession() as session:
            res = await asyncio.gather(Crawler(session=session, test_type='http',url_to_test= 'https://baidu.com').test(),
                                       Crawler(session=session, test_type='dns',url_to_test= 'https://baidu.com').test())
            print(res)
    asyncio.run(main())

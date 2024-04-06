########  base  ########
BASE_DNS_URL_FOR_TEST = 'test.domain.com' # the base url that will be applied to your authoritative DNS server. assume 2.2.2.2 is one of Anycast IPs, it well set 2.2.2.2.domian.com A record 2.2.2.2
CNAME_BASE_URL = {
    'VERCEL':'vercel-cname.domain.com.', # if you use huawei cloud, it must end with a period
    'NETLIFY':'netlify-cname.domain.com.',
    'VERLIFY':'verlify-cname.domain.com.' # conbine vercel and netlify records into one
} 

CNAME_DEFAULT_RECORD = {
    'VERCEL':'76.76.21.21',
    'NETLIFY':'75.2.60.5'
}

CONCURRENCY = 7 # for aiohttp.TCPConnector(limit=CONCURRENCY))

NETLIFY_URL_TO_TEST = 'https://netlif.domain.com/health.html' # for get netlify Anycast IPs
VERCEL_URL_TO_TEST = 'https://vercel.domain.com/health.html' 
OPTIONAL_PATH = '/health.html'
FILTER_CONFIG = {
    'defualt_un_code_200_limit_backup' :2,
    'defualt_time_limit_backup' :2200,
    'Netlify':{
        'dianxin' :{
            'time_limit': 1500, # ms. ignore dns resolve time
            'a_record_count':1,
            'un_code_200_limit':1,
            'time_limit_backup':3000, # 可以不写此参数 You do not need to write this parameter
            'un_code_200_limit_backup' :2 # 可以不写此参数 You do not need to write this parameter
        },
        'liantong': {
            'time_limit': 1100,
            'a_record_count':2,
            'un_code_200_limit':1,
        },
        'yidong':{
            'time_limit': 1100,
            'a_record_count':1,
            'un_code_200_limit':1,
        }
    },
    'Vercel':{
        'dianxin' :{
            'time_limit': 1500, # ms. ignore dns resolve time
            'a_record_count':1,
            'un_code_200_limit':1,
        },
        'liantong': {
            'time_limit': 1100,
            'a_record_count':1,
            'un_code_200_limit':0,
            'un_code_200_limit_backup':1,
        },
        'yidong':{
            'time_limit': 1600,
            'a_record_count':1,
            'un_code_200_limit':1,
        }
    },
}


#########  netlify  ##########
NETLIFY_PAT = '' # Personal access tokens 
NETLIFY_SITE_ID = ''
BASE_NETLIFY_API_URL = 'https://api.netlify.com/api/v1'
UPDATE_NETLIFY_SITE_API_PATH = f'/sites/{NETLIFY_SITE_ID}'
###########  HWcloud  ###############
# https://support.huaweicloud.com/api-iam/iam_30_0001.html#section4
HW_IAM_DOMAIN = ''
HW_IAM_USER = ''
HW_IAM_PWD = ''
HW_PROJECT_ID = ''
HW_HK_REGION_API_BASE_URL = 'https://dns.ap-southeast-1.myhuaweicloud.com' # replace this if needed
HW_ZONE_ID = ''
HW_ADD_ONE_RECORD_PATH = f'/v2/zones/{HW_ZONE_ID}/recordsets'
HW_UPDATE_BATCH_RECORD_WITH_LINES_PATH = F'/v2.1/zones/{HW_ZONE_ID}/recordsets'
HW_CREATE_RECORD_WITH_BATCH_LINES_PATH = F'/v2.1/zones/{HW_ZONE_ID}/recordsets/batch/lines'

#########  vercel  ###########
VERCEL_TOKEN = ''
VERCEL_PROJECT_ID = ''
VERCEL_BASE_API_URL = 'https://api.vercel.com'
VERCEL_ADD_DOMAIN_PATH = F'/v10/projects/{VERCEL_PROJECT_ID}/domains'
###########  DB  ##########
RECORD_HP = 9
REVIVE = 3
REVIVE_PERIOD = 3 # if column hp_{isp} = 0 and column revive_{isp} = 3 when it has more than {REVIVE_PERIOD} days since the last revival, it will test that record


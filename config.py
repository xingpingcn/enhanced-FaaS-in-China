########  base  ########
CNAME_BASE_URL = {
    'VERCEL':'vercel-cname.xingpingcn.top.', # if you use huawei cloud, it must end with a period
    'NETLIFY':'netlify-cname.xingpingcn.top.',
    'VERLIFY':'verlify-cname.xingpingcn.top.' ,# conbine vercel and netlify records into one
    'CF':'cf-cname.xingpingcn.top.'
} 
RES_BACKUP_LENGTH = 6

CNAME_DEFAULT_RECORD = {
    'VERCEL':'76.76.21.21',
    'NETLIFY':'75.2.60.5',
    'CF':'1.1.1.1'
}
CONCURRENCY = 7 # for aiohttp.TCPConnector(limit=CONCURRENCY)
NETLIFY_URL_TO_TEST = ['https://domain.com/test.html'] # for get netlify Anycast IPs
VERCEL_URL_TO_TEST = ['https://domain.com/test.html'] 
CF_URL_TO_TEST = ['']

CF_SELECTED_DOMAIN_LIST = ['']
FILTER_CONFIG = {
    'defualt_un_code_200_limit_backup' :2,
    'defualt_time_limit_backup' :2200,
    'Netlify':{
        'dianxin' :{
            'time_limit': 900, # ms. ignore dns resolve time
            'a_record_count':1,
            'un_code_200_limit':1,
            'time_limit_backup':2400, # 可以不写此参数 You do not need to write this parameter
            'un_code_200_limit_backup' :2 # 可以不写此参数 You do not need to write this parameter
        },
        'liantong': {
            'time_limit': 600,
            'a_record_count':2,
            'un_code_200_limit':1,
        },
        'yidong':{
            'time_limit': 600,
            'a_record_count':1,
            'un_code_200_limit':1,
        }
    },
    'Vercel':{
        'dianxin' :{
            'time_limit': 900, # ms. ignore dns resolve time
            'a_record_count':1,
            'un_code_200_limit':1,
        },
        'liantong': {
            'time_limit': 600,
            'a_record_count':1,
            'un_code_200_limit':0,
            'un_code_200_limit_backup':1,
        },
        'yidong':{
            'time_limit': 600,
            'a_record_count':1,
            'un_code_200_limit':1,
        }
    },
    'Cf':{
        'dianxin' :{
            'time_limit': 1100, # ms. ignore dns resolve time
            'a_record_count':1,
            'un_code_200_limit':2,
            'un_code_200_limit_backup' :3
        },
        'liantong': {
            'time_limit': 1100,
            'a_record_count':1,
            'un_code_200_limit':2,
            'un_code_200_limit_backup' :3
        },
        'yidong':{
            'time_limit': 1600,
            'a_record_count':1,
            'un_code_200_limit':2,
            'un_code_200_limit_backup' :3
        }
    },
}


###########  HWcloud  ###############
# https://support.huaweicloud.com/api-iam/iam_30_0001.html#section4
HW_IAM_DOMAIN = ''
HW_IAM_USER = ''
HW_IAM_PWD = ''
HW_PROJECT_ID = ''
HW_HK_REGION_API_BASE_URL = 'https://dns.ap-southeast-1.myhuaweicloud.com' # replace it if needed

HW_ZONE_ID = '' 
HW_ADD_ONE_RECORD_PATH = f'/v2/zones/{HW_ZONE_ID}/recordsets'
HW_UPDATE_BATCH_RECORD_WITH_LINES_PATH = F'/v2.1/zones/{HW_ZONE_ID}/recordsets'
HW_CREATE_RECORD_WITH_BATCH_LINES_PATH = F'/v2.1/zones/{HW_ZONE_ID}/recordsets/batch/lines'

###########  DB  ##########
RECORD_HP = 9
REVIVE = 3
REVIVE_PERIOD = 3 # if column hp_{isp} = 0 and column revive_{isp} = 3 when it has more than {REVIVE_PERIOD} days since the last revival, it will test that record


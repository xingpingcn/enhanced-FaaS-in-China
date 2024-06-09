#!/bin/bash
PATH=/opt/someApp/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# 需要填写
BASE_PATH=""
# 更改为你的域名
/root/.acme.sh/acme.sh --install-cert -d domain.com \
--key-file      $BASE_PATH/domain.com.key.pem  \
--cert-file $BASE_PATH/domain.com.cert.pem \
--fullchain-file $BASE_PATH/domain.com.fullchain.pem 

# 设置 Netlify API 密钥和站点 ID
NETLIFY_API_KEY=""
NETLIFY_SITE_ID=""

# 获取更新后的证书和私钥文件路径

CERT_PATH=$(cat $BASE_PATH/domain.com.cert.pem)
KEY_PATH=$(cat $BASE_PATH/domain.com.key.pem)
FULLCHAIN_CERT_PATH=$(cat $BASE_PATH/domain.com.fullchain.pem)


# 要输出log要在当前目录先新建一个logs文件夹
# 使用 Netlify API 上传证书
curl  -X POST \
  -H "Authorization: Bearer $NETLIFY_API_KEY" \
  --form-string "key=${KEY_PATH}" \
  --form-string "ca_certificates=${FULLCHAIN_CERT_PATH}" \
  --form-string "certificate=${CERT_PATH}" \
  -o "${BASE_PATH}/logs/$(date "+%Y-%m-%d-%H-%M-%S").json" "https://api.netlify.com/api/v1/sites/${NETLIFY_SITE_ID}/ssl" 
  
  
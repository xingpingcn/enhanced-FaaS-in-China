# 自动上传证书到netlify

## What u need

1. vps或者电脑
1. 你的`netlify api key`

## How to do

1. 下载`acme.sh`用于申请证书。具体下载教程请谷歌。
1. 假设你的证书放在`/home/netlify_cert`，你需要先用`acme.sh`申请证书。[如何申请](https://xingpingcn.top/docker-learning-notes.html#acme-sh)
1. 下载本repo里的`upload_netlify_cert.sh`到你的一个文件夹，假设为`/home/netlify_cert`，打开`upload_netlify_cert.sh`填写相关配置
1. 下载本repo里的`upload-per-7d`并且放到`/etc/cron.d`，这个是用于每个星期上传证书的。放到这里就可以了，但是需要打开该文件看看路径是否正确。注意是用root用户运行的。

## Test

对于`upload_netlify_cert.sh`，运行

```bash
/home/netlify_cert/upload_netlify_cert.sh
```

看一下是否成功。注意路径。

对于`upload-per-7d`，你可以参看当前的时间，例如现在是`8:01`，那么你就修改为

```bash
3 * * * * root /bin/bash /home/netlify_cert/upload_netlify_cert.sh >/tmp/test.log 2>&1
```

意思是每个小时的第3分钟执行一次。等两分钟之后查看logs里面的json

或者输入

```bash
cat /tmp/test.log
```

查看。

成功了再把命令改回去。

# enhanced-FaaS-in-China

Improve the access speed and stability in China of web pages deployed in vercel <br>
提升部署在vercel或netlify的网页在中国的访问速度和稳定性

## Usage

* 如果你的网站部署在`vercel`，则把cname记录改为：
  * `vercel-cname.xingpingcn.eu.org`
* 如果你的网站部署在`netlify`，则把cname记录改为：
  * `netlify-cname.xingpingcn.eu.org`
* 如果你的网站部署在`netlify`和`vercel`上，则把cname记录改为：
  * `verlify-cname.xingpingcn.eu.org`
  * 使用此dns解析建议：先把cname记录改为官方提供的url，等`ssl/tls证书`生成之后再把cname记录改为`verlify-cname.xingpingcn.eu.org`

## Why to use it

1. 如果在大陆访问，官方的anycast会将流量大概率路由到东南亚，路线压力很大，但是存在压力较小的美国或者欧洲的路线。
1. 由于存在被墙风险，如果使用单一的平台——例如vercel——则会存在全军覆没的情况，既国内所有地方都不能访问你的网站。

## How it works

选取vercel和netlify的IP，定时测试速度，选取稳定且快的ip添加到域名的A记录。国内有三网优化，国外统一使用官方提供的A记录。

大概每一小时更新一次。

IP来源

* vercel
  * [vercel ip](https://gist.github.com/ChenYFan/fc2bd4ec1795766f2613b52ba123c0f8)
  * 官方`cname.vercel-dns.com.`的A记录
* netlify
  * 官方所提供的链接的A记录

## Q&A

Q：为什么分路线解析不准确？<br>
A：我使用的是权威DNS服务器自带的路线解析，可能存在误判。如果你想要更加精准的分路线解析，可以自行选取其他DNS服务器——如dnspod——并添加[Netlify.json](https://raw.githubusercontent.com/xingpingcn/enhanced-FaaS-in-China/main/Netlify.json)或[Vercel.json](https://https://raw.githubusercontent.com/xingpingcn/enhanced-FaaS-in-China/main/Vercel.json)里的IP到A记录。或使用`NS1.COM`作为权威DNS服务器，并设置根据`ASN`进行路线解析。你可以看看我写的[ASN列表](https://github.com/xingpingcn/china-mainland-asn)。<br>

Q：为什么设置了你的CNAME解析后网站不能访问？<br>
A：

* 这大概率是使用了`verlify-cname.xingpingcn.eu.org`导致的。需要先把CNAME记录改为官方提供的链接，等待SSL证书生成后再重新设置。这是由于该解析包含两个平台的IP，平台每次访问都会获得二者之一的IP，因而认为你在平台所填写的域名并不是你所拥有的。但是一旦生成证书后，证书就会缓存在平台上。
* netlify支持上传自己的证书。如果还是不行就申请一个能自动续期的证书。

## Custom

如果你想自定义，例如增加第三个平台，如`render`、`railway`等，则需要自己准备测速工具和一个域名，并重写`crawler.py`，在`platforms_to_update`新建一个`.py`文件，仿照文件夹内的其他文件重写`update()`方法，最后修改`config.py`文件相关配置。
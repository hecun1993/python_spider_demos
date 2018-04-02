from urllib.parse import urlencode
import pymongo
import requests
from lxml.etree import XMLSyntaxError
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from Weixin.config import *


'''
http://weixin.sogou.com/weixin?query=%E5%92%8C%E8%8F%9C%E5%A4%B4&type=2&page=2&ie=utf8
只需要在链接中留下：query，type，page，ie即可

在11页之后，需要用微信登录后才可以查看，所以需要获取cookie信息

会需要输入三次验证码，其页面是302跳转，这说明ip被封，需要用代理池

'''

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

base_url = 'http://weixin.sogou.com/weixin?'

# 因为要登陆才能查看，所以需要cookie信息
headers = {
    'Cookie': 'SUID=F6177C7B3220910A000000058E4D679; SUV=1491392122762346; ABTEST=1|1491392129|v1; SNUID=0DED8681FBFEB69230E6BF3DFB2F8D6B; ld=OZllllllll2Yi2balllllV06C77lllllWTZgdkllll9lllllxv7ll5@@@@@@@@@@; LSTMV=189%2C31; LCLKINT=1805; weixinIndexVisited=1; SUIR=0DED8681FBFEB69230E6BF3DFB2F8D6B; JSESSIONID=aaa-BcHIDk9xYdr4odFSv; PHPSESSID=afohijek3ju93ab6l0eqeph902; sct=21; IPLOC=CN; ppinf=5|1491580643|1492790243|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyNzolRTUlQjQlOTQlRTUlQkElODYlRTYlODklOER8Y3J0OjEwOjE0OTE1ODA2NDN8cmVmbmljazoyNzolRTUlQjQlOTQlRTUlQkElODYlRTYlODklOER8dXNlcmlkOjQ0Om85dDJsdUJfZWVYOGRqSjRKN0xhNlBta0RJODRAd2VpeGluLnNvaHUuY29tfA; pprdig=j7ojfJRegMrYrl96LmzUhNq-RujAWyuXT_H3xZba8nNtaj7NKA5d0ORq-yoqedkBg4USxLzmbUMnIVsCUjFciRnHDPJ6TyNrurEdWT_LvHsQIKkygfLJH-U2MJvhwtHuW09enCEzcDAA_GdjwX6_-_fqTJuv9w9Gsw4rF9xfGf4; sgid=; ppmdig=1491580643000000d6ae8b0ebe76bbd1844c993d1ff47cea',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
}

# 全局变量
proxy = None

# 获取代理ip的方法（直接请求flask的网页，获取网页内容）
def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

# 获取列表页的html源码
def get_html(url, count=1):
    print('Crawling', url)
    print('Trying Count', count)

    # 引用全局变量，刚开始proxy是None，就是直接爬取
    global proxy

    # 判断最大请求次数
    if count >= MAX_COUNT:
        print('Tried Too Many Counts')
        return None
    try:
        # 这里是请求页面的逻辑，有代理/没有代理
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            # allow_redirects=False 不要默认处理跳转，也就是不要跳转到302页面（输入验证码）
            response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies)
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)

        # ip正常
        if response.status_code == 200:
            return response.text

        if response.status_code == 302:
            # Need Proxy 即使用了代理，也302，说明需要新的代理
            print('302')
            # 重新获取代理
            proxy = get_proxy()
            if proxy:
                print('Using Proxy', proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None

    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        # 尝试次数加1
        count += 1
        # 获取失败，递归调用自己，重试
        return get_html(url, count)

# 爬取列表页，主要是构造请求的url
def get_index(keyword, page):
    # 构造请求参数
    data = {
        'query': keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html

# 解析列表页
def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

# 获取详情页
def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

# 解析详情页
def parse_detail(html):
    try:
        doc = pq(html)

        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content').text()
        date = doc('#post-date').text()
        nickname = doc('#js_profile_qrcode > div > strong').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title': title,
            'content': content,
            'date': date,
            'nickname': nickname,
            'wechat': wechat
        }
    except XMLSyntaxError:
        return None

def save_to_mongo(data):
    # True 存在就更新，不存在就插入
    if db['articles'].update({'title': data['title']}, {'$set': data}, True):
        print('Saved to Mongo', data['title'])
    else:
        print('Saved to Mongo Failed', data['title'])

def main():
    for page in range(1, 101):
        html = get_index(KEYWORD, page)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    print(article_data)
                    if article_data:
                        save_to_mongo(article_data)

if __name__ == '__main__':
    main()

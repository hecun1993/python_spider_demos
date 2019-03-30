import requests
import json
import re
import random
import time
from lxml.etree import XMLSyntaxError
from pyquery import PyQuery as pq
import pymongo
import config

client = pymongo.MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB]

def parse_first(gzlist):
    url = 'https://mp.weixin.qq.com'
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
    }

    with open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
    cookies = json.loads(cookie)

    response = requests.get(url=url, cookies=cookies)
    token = re.findall(r'token=(\d+)', str(response.url))[0]

    # 第一步：输入账号的微信号，查找到这个账号
    for query in gzlist:
        query_id = {
            'action': 'search_biz',
            'token' : token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'query': query,
            'begin': '0',
            'count': '5',
        }

        search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
        search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)

        # search_response是响应内容，本身响应的就是一个json，所以，可以使用response的json方法，获取list键对应的值，其实就是搜索公众号的结果，数据类型是一个列表，然后取第一个元素，就是搜索到的账号
        lists = search_response.json().get('list')[0]
        # fakeid相当于公众号的标识，在json的list键值中（数据类型是一个字典）
        fakeid = lists.get('fakeid')

        # 开始构造第二次请求，就是点击搜索到的账号，就会出现所有已推送文章的列表
        # 要带上公众号的标识fakeid
        query_id_data = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin': '0',
            'count': '5',
            'query': '',
            'fakeid': fakeid,
            'type': '9'
        }
        # 构造请求，因为已经有了参数
        appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
        appmsg_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
        # 公众号已经推送的图文消息总量
        max_num = appmsg_response.json().get('app_msg_cnt')
        # 获取页数，num + 1就是
        num = int(int(max_num) / 5)

        # 开始爬取，带翻页
        begin = 0
        while num + 1 > 0 :
            query_id_data = {
                'token': token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': random.random(),
                'action': 'list_ex',
                # 构造翻页，改变begin的值即可
                'begin': '{}'.format(str(begin)),
                'count': '5',
                'query': '',
                'fakeid': fakeid,
                'type': '9'
            }

            print('翻页###################',begin)
            query_fakeid_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
            fakeid_list = query_fakeid_response.json().get('app_msg_list')

            # 得到每篇文章的url，即可进行下一步的爬取了
            for item in fakeid_list:
                # 构造生成器
                print(item.get('link'))
                yield item.get('link')

            num -= 1
            begin = int(begin)
            begin += 5
            time.sleep(2)


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
    # gzlist = ['bitsea', 'fdu-hecun']
    gzlist = ['ANT-Fin-Recruitment']
    urls = parse_first(gzlist=gzlist)
    for url in urls:
        article_html = get_detail(url)
        if article_html:
            article_data = parse_detail(article_html)
            print(article_data)
            if article_data:
                save_to_mongo(article_data)

if __name__ == '__main__':
    a = "s"
    if a is "s":
        print(123)
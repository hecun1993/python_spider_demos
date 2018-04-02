import json
import os
import pymongo
import re
import requests
from bs4 import BeautifulSoup
from hashlib import md5
from json.decoder import JSONDecodeError
from multiprocessing import Pool
from requests.exceptions import ConnectionError
from urllib.parse import urlencode

from toutiao.config_toutiao import *

# 防止多线程爬取时的pymongo的警告，加了connect=False
client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

# 获取列表页的url
# 因为后续的页面是通过ajax请求完成的,所以,最初的页面的参数,需要下拉页面之后,在获得ajax请求的数据后,找到最初的那一页的请求参数
# offset和keyword是可变的参数，需要组成字典传入。
# http://www.toutiao.com/search/?keyword=%E8%A1%97%E6%8B%8D
def get_page_index(offset, keyword):
    data = {
        'autoload': 'true',
        'count': 20,
        'cur_tab': 3,
        'format': 'json',
        'keyword': keyword,
        'offset': offset,
    }
    # http://www.toutiao.com/search_content/?offset=20&format=json&keyword=%E8%A1%97%E6%8B%8D&autoload=true&count=20&cur_tab=3
    # urlencode() 把字典变成url链接的后面的部分，上面的data就是请求时url后面携带的参数,是urllib库自带的方法,就是构造一个链接
    # 因为原本的链接只是http://www.toutiao.com/search/?keyword=%E8%A1%97%E6%8B%8D
    # 而实际的请求链接需要有ajax的请求参数
    params = urlencode(data)
    base = 'http://www.toutiao.com/search_content/'
    url = base + '?' + params
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        print('Error occurred')
        return None

# 解析返回的每一个列表页html，获取详情页的url
def parse_page_index(text):
    try:
        # 把json字符串text转化成json对象data
        data = json.loads(text)
        # 判断data在所有的键名中
        if data and 'data' in data.keys():
            for item in data.get('data'):
                # 对列表页，我们只需要拿到详情页的url即可
                yield item.get('article_url')
    except JSONDecodeError:
        pass

# 获取详情页的html
def get_page_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        print('Error occurred')
        return None

# 解析详情页的html，获取title和详情页图集的每一个图片，当然还有本详情页的url
# http://www.toutiao.com/a6427974363517567233/#p=1
# 这个才是要提取的详情页的内容,因为其直接回返回到html源代码中,所以,用正则表达式就可以匹配.
# 存在了var gallery = {}的js中
def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    # 提取组图的名称
    # soup.select("title")[0].get_text() 获取到了文本信息，下面的两句等价于这一句
    result = soup.select('title')
    title = result[0].get_text() if result else ''
    # 用re来解析html源代码(因为图片的信息在js里,就没有办法通过pyquery等解析,所以用正则匹配)
    images_pattern = re.compile('var gallery = (.*?);', re.S)
    result = re.search(images_pattern, html)

    if result:
        # 先把字符串变成json对象
        data = json.loads(result.group(1))
        # 看sub_images的键名是否存在
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            # 获取了很多的image链接,构成一个数组
            images = [item.get('url') for item in sub_images]
            # 下载图片
            for image in images: download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }

# 把数据保存到数据库中
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('Successfully Saved to Mongo', result)
        return True
    return False

# 保存图片的第一步，就是获得response对象，然后再调用save方法，传入response.content获取到的二进制内容，进行保存
def download_image(url):
    print('Downloading', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except ConnectionError:
        return None

# 保存图片，要传入response.content的二进制文件，然后再用f.write()写入
def save_image(content):
    # 第一个参数，当前项目位置
    # 第二个参数，为了不会有图片重复,只要内容一样,名称就一样，这样就不会下载到重复的内容，因为文件名相同，就会覆盖了.用md5(content).hexdigest()
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    text = get_page_index(offset, KEYWORD)
    urls = parse_page_index(text)
    for url in urls:
        html = get_page_detail(url)
        # 这里没有对结果进行遍历，所以，不需要构造成yield，直接return即可
        result = parse_page_detail(html, url)
        if result: save_to_mongo(result)

if __name__ == '__main__':
    pool = Pool()
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)
    pool.close()
    pool.join()

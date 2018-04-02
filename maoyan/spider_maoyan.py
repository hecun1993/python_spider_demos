import json
from multiprocessing import Pool
import requests
import time
from requests.exceptions import RequestException
import re

def get_one_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

## 按照正则表达式匹配时，要看源代码，而不是检查元素！！

def parse_one_page(html):
    # 传入的是字符串，转化为re对象
    # re.S 匹配任意字符，包括换行符
    # pattern相当于匹配规则，而html(通过requests.get()获得的源代码)是需要匹配的字符串
    # .*?就是匹配任意多个字符
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         +'.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         +'.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    # 这里的返回值是一个由元组构成的列表
    # [('1', 'www.http.com'...), (), ()]
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2],
            'actor': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5]+item[6]
        }

def write_to_file(content):
    with open('result1.txt', 'a', encoding='utf-8') as f:
        # 把上面用yield形成的字典形式的content转成字符串，用json.dumps(content)
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()

def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


if __name__ == '__main__':
    # pool = Pool()
    # # map()的第二个参数必须是列表
    # pool.map(main, [i*10 for i in range(10)])
    # pool.close()
    # pool.join()
    #
    # for i in range(10):
    #     main(offset=i * 10)
    #     time.sleep(5)

    main(0)
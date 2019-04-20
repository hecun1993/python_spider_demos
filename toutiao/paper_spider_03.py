import json
import requests
from bs4 import BeautifulSoup

import jieba

def parse(param):
    detail_data = requests.get(param)
    result = BeautifulSoup(detail_data.text, "lxml")

    try:
        content = result.select('#vdetail_sum_p')[0].text.strip().replace('\n', '').replace('\r', '') if result.select(
                '#vdetail_sum_p') else None

        print({'content': content})
        write_to_file(content)
    except:
        return None


def write_to_file(content):
    with open('content.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()


if __name__ == '__main__':

    column_list_num = ['72902']

    const_page_url_prefix = 'https://m.thepaper.cn/topicList.jsp?n='
    const_page_url_suffix = '&c=72900'
    for num in column_list_num:
        page_url = const_page_url_prefix + num + const_page_url_suffix

        print(page_url)

        wb_data = requests.get(page_url)
        soup = BeautifulSoup(wb_data.text, "lxml")

        for link in soup.select('.topicmore_title a'):
            item = link.get('href')
            const_detail_url = 'https://m.thepaper.cn/'
            link_url = const_detail_url + item
            parse(link_url)

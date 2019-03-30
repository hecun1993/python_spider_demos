import json
import requests
from bs4 import BeautifulSoup
import pymongo

MONGO_URL = 'localhost'
MONGO_DB = 'paper'

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def save_to_mongo(data):
    # True 存在就更新，不存在就插入
    if db['article2'].update({'title': data['title']}, {'$set': data}, True):
        print('Saved to Mongo', data['title'])
    else:
        print('Saved to Mongo Failed', data['title'])


def parse(param):
    detail_data = requests.get(param)
    result = BeautifulSoup(detail_data.text, "lxml")

    try:
        comments_count = len(result.select('.name'))

        if comments_count > 0:
            title = result.title.text if result.title else None
            person = result.select('.news_video_name')[1].text.strip().replace('\n', ' ').replace('\xa0', ' ') if result.select('.news_video_name') else None
            time = result.select('.news_video_name')[1].text.strip().replace('\n', ' ').replace('\xa0', ' ') if result.select('.news_video_name') else None
            content = result.select('#vdetail_sum_p')[0].text.strip().replace('\n', '').replace('\r', '') if result.select(
                '#vdetail_sum_p') else None
            column = result.select('.gg-gmcont a')[0].text.strip() if result.select('.gg-gmcont a') else None
            dz = result.select('.dz')[0].text.strip() if result.select('.dz') else None

            comments = ''

            for i in range(comments_count):
                try:
                    comment_time = result.select('.name')[i].select('.user_time')[0].text.strip().replace('\n', ' ').replace('\xa0', ' ')
                    comment_person = result.select('.name')[i].select('div')[0].text.strip().replace('\n', ' ').replace('\xa0', ' ')
                    comment_content = result.select('.hot_talk_item')[i].select('.con')[0].text.strip().replace('\n', '').replace('\r', '')
                    comment_praise = result.select('.hot_talk_item')[i].select('.user_header_praise')[0].text.strip()

                    comments = comments + comment_time + "|" + comment_person + "|" + comment_content + "|" + comment_praise + "|"
                except:
                    continue

            print({'title': title, 'person': person, 'time': time, 'content': content,
                   'column': column,
                   'dz': dz, 'url': param, 'comments': comments})

            save_to_mongo(
                {'title': title, 'person': person, 'time': time, 'content': content,
                 'column': column,
                 'dz': dz, 'url': param, 'comments': comments})
        else:
            title = result.title.text if result.title else None
            person = result.select('.news_video_name')[1].text.strip().replace('\n', ' ').replace('\xa0', ' ') if result.select('.news_video_name') else None
            time = result.select('.news_video_name')[1].text.strip().replace('\n', ' ').replace('\xa0', ' ') if result.select('.news_video_name') else None
            content = result.select('#vdetail_sum_p')[0].text.strip().replace('\n', '').replace('\r', '') if result.select(
                '#vdetail_sum_p') else None
            column = result.select('.gg-gmcont a')[0].text.strip() if result.select('.gg-gmcont a') else None
            dz = result.select('.dz')[0].text.strip() if result.select('.dz') else None

            print({'title': title, 'person': person, 'time': time, 'content': content,
                   'column': column,
                   'dz': dz, 'url': param, 'comments': None})

            save_to_mongo(
                {'title': title, 'person': person, 'time': time, 'content': content,
                 'column': column,
                 'dz': dz, 'url': param, 'comments': None})
    except:
        return None


def write_to_file(content):
    with open('paper_news_result_02.csv', 'a', encoding='utf-8') as f:
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

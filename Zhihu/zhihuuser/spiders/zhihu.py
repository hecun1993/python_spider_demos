# -*- coding: utf-8 -*-
import json

from scrapy import Spider, Request
from zhihuuser.items import UserItem

'''

从github上clone之后,新建分支
    git checkout -b distributed
    git branch
    
    git status
    git add -A
    git commit -m "add distributed"
    git push origin distributed
    
    git clone 地址 -b distributed
    
    git pull origin distributed 更新

先测试两部:
    第一是用户的详细信息,看是否可以返回
    第二是用户的关注列表,看是否可以返回(oauth头)

scrapy startproject zhihuuser
scrapy genspider zhihu www.zhihu.com
scrapy crawl zhihu

执行会报错：www.zhihu.com/robots.txt
要在scrapy中把True改成False（settings.py）

再运行会继续报错
因为缺少headers的信息。
在知乎中，找到headers信息：
User-Agent : Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36
放在settings.py中
这样就可以返回200状态码，成功。

'''

class ZhihuSpider(Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'

    # 变成通用形式的url，用format函数
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'

    start_user = 'tianshansoft'

    # include
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,answer_count,articles_count,pins_count,question_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'

    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    # 生成爬取的url链接
    # 先爬取某个人的详细信息，再爬取这个人的关注列表
    def start_requests(self):
        # 回调函数用来解析用户的详细信息
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, limit=20, offset=0),
                      self.parse_follows)
        yield Request(self.followers_url.format(user=self.start_user, include=self.followers_query, limit=20, offset=0),
                      self.parse_followers)

    # 解析用户的详细信息，比如工作地点，关注领域等
    # response返回的是一个json格式的，所以需要先变成对象
    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()

        # 存储数据
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item

        # 再请求每一个关注者的关注列表，include=self.follows_query
        yield Request(
            self.follows_url.format(user=result.get('url_token'), include=self.follows_query, limit=20, offset=0),
            self.parse_follows)

        yield Request(
            self.followers_url.format(user=result.get('url_token'), include=self.followers_query, limit=20, offset=0),
            self.parse_followers)

    # 相当于爬取关注者的列表页，得到一个个的关注用户
    # 解析follows的列表
    def parse_follows(self, response):
        results = json.loads(response.text)

        # 解析用户的具体信息
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)

        # 爬取下一页的follows
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_follows)

    def parse_followers(self, response):
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)

            # 判断是否有下一页的关注列表
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_followers)

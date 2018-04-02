import pymongo
import re
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from taobao.config_taobao import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# 用selenium中的webdriver ChromeDriver
browser = webdriver.Chrome()
# 设定最长的等待时间，如果超过10秒没有加载出来，就会抛出异常
wait = WebDriverWait(browser, 10)

def search():
    try:
        browser.get("https://www.taobao.com")

        # 选中搜索框：presence_of_element_located
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )

        # 选中提交按钮：element_to_be_clickable
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )

        input.send_keys("美食")
        submit.click()

        get_products()

        # 等到搜索结果页面里的"共100页"加载出来之后，再进行操作
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )

        # 返回总页数："共100页"，后续需要在main方法中，用正则提取出100这个数字
        # total = int(re.compile('(\d+)').search(total).group(1))
        return total.text

    except TimeoutException:
        return search()

# 直接在输入页数的框中输入页数，就可以搜索到下一页了
# 不用按翻页按钮，容易在程序暂停时发生混乱
def next_page(page_number):
    try:
        # 输入页数的框
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        # 提交按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        # 先清除内容，再输入页数
        input.clear()
        input.send_keys(page_number)
        submit.click()
        # 此时，执行了翻页操作

        # 判断是否翻页成功：比较输入页码框和高亮部分的内容是否相同
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
        )
        get_products()

    except TimeoutException:
        next_page(page_number)

def get_products():
    # 判断是否所有的宝贝信息都加载成功了
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )
    html = browser.page_source
    # 解析网页源代码
    doc = pq(html)
    # 得到所有选择的内容：items()
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储失败', result)

def main():
    # search()
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    print(total)
    for i in range(2, total + 1):
        next_page(i)

    browser.close()

if __name__ == '__main__':
    main()

import time
import json
from selenium import webdriver

post = {}

driver = webdriver.Chrome()
driver.get('https://mp.weixin.qq.com/')
time.sleep(2)
# 获取登录框和密码框
driver.find_element_by_xpath("./*//input[@name='account']").clear()
driver.find_element_by_xpath("./*//input[@name='account']").send_keys('hecun93@gmail.com')
driver.find_element_by_xpath("./*//input[@name='password']").clear()
driver.find_element_by_xpath("./*//input[@name='password']").send_keys('hc930807'
                                                                '')
# 在自动输完密码之后记得点一下记住我，保存cookie
time.sleep(5)
# 点击登录
driver.find_element_by_xpath("./*//a[@class='btn_login']").click()
# 拿手机扫二维码！
time.sleep(15)

cookie_items = driver.get_cookies()
for cookie_item in cookie_items:
    post[cookie_item['name']] = cookie_item['value']
cookie_str = json.dumps(post)
with open('cookie.txt', 'w+', encoding='utf-8') as f:
    f.write(cookie_str)
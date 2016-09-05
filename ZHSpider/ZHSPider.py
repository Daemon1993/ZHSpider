import pymongo
import requests
import time

try:
    import cookielib
except:
    import http.cookiejar as cookielib

from ZHSpider import LoginActon,DataParseAction
from bs4 import BeautifulSoup, SoupStrainer


headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
    'Host': "www.zhihu.com",
    'Origin': "http://www.zhihu.com",
    'Pragma': "no-cache",
    'Referer': "http://www.zhihu.com/"
}

# 使用登录cookie信息 如果存在cookie 带上最近的cookie
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")

#连接数据库 用于数据存储
client = pymongo.MongoClient('localhost', 27017)
db = client['local']
zh = db['ZHUserInfo']


#获取个人主页url 亦用于login status
def getMyCenterURL():

    try:
        html=session.get(LoginActon.index_url,headers=headers)
        zu_top = SoupStrainer(class_="zu-top")
        soup=BeautifulSoup(html.text,'lxml',parse_only=zu_top)
        #获取个人主页 前面个人主页页面
        a_info=soup.find('a',class_='zu-top-nav-userinfo')
        my_home_href=LoginActon.index_url+a_info.get('href')
        print("login ok my home url is {0}".format(my_home_href))
    except:
        return False

    print(my_home_href)
    start=time.time()


    DataParseAction.saveDataByUrl(my_home_href, my_home_href, headers, zh, 0)

    DataParseAction.startSpider(session,headers,zh)

    elapsed=time.time()-start
    print('All time {0}  size{1}'.format(elapsed,zh.count()))

    return True




if __name__ == '__main__':
    account = 'phone or email'
    secret = 'XXOO'
    refer="http://www.zhihu.com/"
    if(getMyCenterURL()):
        #登陆状态
        pass
    else:
        LoginActon.login(secret,account,session,headers)
        getMyCenterURL()


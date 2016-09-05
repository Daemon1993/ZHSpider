import random
import time
import gevent
import pymongo
import requests

__author__ = 'Daemon1993'

from bs4 import BeautifulSoup, SoupStrainer
from ZHSpider import LoginActon
from ZHSpider import getProxyIP

'''
解析 用户主页数据
parmas url userHomePage
get all attention users
'''

# 全局 count 每次解析一个 就加一
count = 0
sleep_time = 0
sleep_timeCount = 0

# tagName_ClassName 获取相关数据
def getTagTextByName_Class(soup, tagName, class_name, data, key):
    try:
        value = soup.find(tagName, class_=class_name).text
        data[key] = value
    except Exception as e:
        pass

# getTitle by Name_Class
def getTagTitleByName_Class(soup, tagName, class_name, data, key):
    try:
        value = soup.find(tagName, class_=class_name).get('title')
        data[key] = value
    except:
        pass

def getSexByName_Class(soup, tagName, class_name, data, key):
    try:
        data[key] = "未知"
        value = soup.find(tagName, class_=class_name)
        value = value.find('i')
        tags = value.get('class')
        tag_str = "".join(tags)

        if (tag_str.find('female') != -1):
            data[key] = "female"
        else:
            data[key] = "male"
    except:
        pass


# 获取关注详情
def getFollowsDetail(soup, tag1, class1, tag2, class2, data, attr_name, key):
    try:
        data[key] = LoginActon.index_url + soup.find(tag1, class_=class1).find(tag2, class_=class2).get(attr_name)
        # 获取 关注信息
        index = 0
        for tag in soup.find(tag1, class_=class1).find_all("strong"):
            if (index == 0):
                data["followees"] = tag.text
            else:
                data["followers"] = tag.text
            index += 1
    except:
        return False
        pass

def getAttentionContent(soup, data):
    try:
        topics = []
        for img in soup.find("div", class_="zm-profile-side-topics").find_all("img"):
            topics.append(img.get('alt'))
        data["topics"] = topics
    except:
        pass

def changeRefer(headers,refer):
    headers["Referer"]=refer


# 根据URL获取 数据 解析保存
def saveDataByUrl(from_url, url, headers, zh, relation_level):
    data = {}

    data['_id'] = url
    data['from_url'] = from_url

    global sleep_time
    if(sleep_time!=0):
        sleep_time=random.randint(0,5)
        if(sleep_time>3):
            print('sleep {0}'.format(sleep_time))
        time.sleep(sleep_time)

    r = requests.session()

    try:
        if(from_url!=url):
            changeRefer(headers,from_url)

        html = r.get(url,timeout=5.0, headers=headers)
    except Exception as e:
        print("saveDataByUrl {0}".format(e))
        return
        pass


    only_data_info = SoupStrainer("div", class_="zm-profile-header-main")

    soup_info = BeautifulSoup(html.text, "lxml", parse_only=only_data_info)

    getTagTextByName_Class(soup_info, "span", "name", data, "name")
    getTagTitleByName_Class(soup_info, "div", "bio ellipsis", data, "introduction")
    getTagTitleByName_Class(soup_info, "span", "location item", data, "location")
    getTagTitleByName_Class(soup_info, "span", "business item", data, "business")

    getSexByName_Class(soup_info, "span", "item gender", data, "gender")

    getTagTitleByName_Class(soup_info, "span", "employment item", data, "work_adr")
    getTagTitleByName_Class(soup_info, "span", "position item", data, "work_direction")
    getTagTitleByName_Class(soup_info, "span", "education item", data, "education_school")
    getTagTitleByName_Class(soup_info, "span", "education-extra item", data, "education_direction")

    try:
        description = soup_info.select('span[class="description unfold-item"] span[class="content"]')[0].get_text()
        data["description"] = description
    except Exception as e:
        pass

    # 关注行为
    only_data_action = SoupStrainer("div", class_="zu-main-sidebar")
    soup_action = BeautifulSoup(html.text, "lxml", parse_only=only_data_action)

    getFollowsDetail(soup_action,
                                  "div", "zm-profile-side-following zg-clear",
                                  "a", "item",
                                  data, "href", "followees_url")

    # 获取关注话题
    getAttentionContent(soup_action, data)
    global count

    try:
        data["relation_level"] = relation_level
        # 当前账号 的关注账号 默认没有被全部加载
        data["followees_status"] = False

        if(count%50==0):
            print(data)
        #200一次随机大于 不停 小于停
        if(count%200==0):
            if(sleep_time>3):
                sleep_time=0
            else:
                sleep_time=random.randint(0,5)

        zh.insert(data)
    except:
        pass

    count += 1
    return True


def startSpider(session, headers, zh):
    print('知乎爬虫 开始工作 ------ 飞起来。。。。')

    # 获取当前DBzhong status=False的所有URL 最大5000
    while True:
        tasks = []
        userinfo= zh.find_one({"followees_status": False})
        if(userinfo is None):
            break
        from_url = userinfo['_id']
        try:
            followees_url = userinfo['followees_url']
        except:
            zh.remove(from_url)
            print('delete {0} '.format(from_url))
            continue
            pass
        relation_level = userinfo['relation_level']

        tasks.append(gevent.spawn(getAllAtentionUsers,
                                  from_url, followees_url, session, headers, zh, relation_level + 1,userinfo))

        gevent.joinall(tasks)


# 获取当前所有的关注用户列表 返回
def getAllAtentionUsers(from_url, follows_url, session, headers, zh, relation_level,userinfo):
    if (follows_url is None):
        return
    html = ""
    r = requests.session()
    r.cookies = session.cookies

    try:
        changeRefer(headers,from_url)

        html = r.get(follows_url, timeout=5.0, headers=headers).text
    except Exception as e:
        pass

    relation_info = SoupStrainer("div", class_="zm-profile-section-wrap zm-profile-followee-page")
    soup = BeautifulSoup(html, "lxml", parse_only=relation_info)

    urls = []
    for user in soup.find_all("div", class_="zm-profile-card zm-profile-section-item zg-clear no-hovercard"):
        user_a = user.find("a")
        url = LoginActon.index_url + user_a.get('href')
        urls.append(url)


    # 保存每个关注的用户信息
    print('user {0} follows size{1} '.format(from_url, len(urls)))

    tasks = [gevent.spawn(saveDataByUrl, from_url, url, headers, zh, relation_level) for url in urls]
    gevent.joinall(tasks)

    try:
        userinfo["followees_status"]=True
        zh.save(userinfo)
    except:
        pass

    print('用户 {0} followees save OK  save count {1}'.format(from_url, count))







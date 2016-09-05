import os
import re
from PIL import Image
from bs4 import BeautifulSoup
import time
from pytesseract import pytesseract

__author__ = 'Daemon1993'


index_url = 'http://www.zhihu.com'
# 获取动态生成的xsrf
def get_xsrf(session,headers):
    '''_xsrf 是一个动态变化的参数'''
    # 获取登录时需要用到的_xsrf
    index_page = session.get(index_url+"/#signin", headers=headers)
    html = index_page.text
    soup = BeautifulSoup(html, 'lxml')
    value = soup.select('input[name="_xsrf"]')
    return value[0].attrs['value']

# 获取验证码
def get_captcha(type,session,headers):
    print('需要验证码 开始获取验证码 type {0}'.format(type))

    t = str(int(time.time() * 1000))
    captcha_url = 'http://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    print('{0} 验证码获取成功 {1}'.format(r, captcha_url))
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()

        im = Image.open('captcha.jpg')
        captcha = 0
        if type == 0:
            captcha = pytesseract.image_to_string(im)
        else:
            im.show()
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
            captcha = input("验证码识别率低 请手动输入 a\n>")
        im.close()

        return captcha


def login(secret, account,session,headers):
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", account):
        print("手机号登录 {0}\n".format(account))
        post_url = 'http://www.zhihu.com/login/phone_num'
        postdata = {
            '_xsrf': get_xsrf(session,headers),
            'password': secret,
            'remember_me': 'true',
            'phone_num': account,
        }
    else:
        print("邮箱登录 {0}\n".format(account))
        post_url = 'http://www.zhihu.com/login/email'
        postdata = {
            '_xsrf': get_xsrf(session,headers),
            'password': secret,
            'remember_me': 'true',
            'email': account,
        }

    # 不需要验证码直接登录成功
    print('登陆数据 {0}'.format(postdata))

    login_page = session.post(post_url, data=postdata, headers=headers)
    login_code = eval(login_page.text)
    recode = login_code['r']
    if (recode == 0):
        print(login_code)

    else:
        print('需要验证码 开始验证码策略')
        count = 0
        while (True):
            # 需要输入验证码后才能登录成功
            captcha = 0
            if count > 1:
                print('第{0}次获取验证码识别错误 2S 后 再次获取验证码 '.format(count + 1))
                if count >= 2:
                    # 开始手动输入
                    captcha = get_captcha(1,session,headers)
                else:
                    captcha = get_captcha(0,session,headers)
            else:
                captcha = get_captcha(0,session,headers)

            postdata["captcha"] = captcha
            print('验证码传入 {0}'.format(captcha))

            login_page = session.post(post_url, data=postdata, headers=headers)
            login_code = eval(login_page.text)

            print(login_code)

            recode = login_code['r']
            if (recode == 0):
                break

            count += 1
            time.sleep(3)

    session.cookies.save()


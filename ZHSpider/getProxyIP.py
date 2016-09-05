from bs4 import BeautifulSoup
import gevent
import pymongo
import requests

headers = {'User-Agent':'Mozilla/5.0 (X11; U; Linux i686)Gecko/20071127 Firefox/2.0.0.11'}

def getIps():
    datas=[]
    for page in range(1, 160):
        try:
            socket= requests.get('http://www.xici.net.co/nn/' + str(page),headers=headers)
            html_doc=socket.text
            print(html_doc)
            soup = BeautifulSoup(html_doc,"lxml")
            trs = soup.find('table', id='ip_list').find_all('tr')
            for tr in trs[1:]:
                tds = tr.find_all('td')
                ip = tds[1].text.strip()
                port = tds[2].text.strip()
                protocol = tds[5].text.strip()
                if protocol == 'HTTP' or protocol == 'HTTPS':
                    data={}
                    data['protocol']=protocol
                    data['ip']=ip
                    data['port']=port
                    datas.append(data)
        except Exception as e:
            print(e)
        if(len(datas)%100):
            print(" "+str(len(datas)))
    return datas

def test(data,ip_client):

    proxy = {'http': 'http://' + data["ip"]+":"+data["port"]}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        url = 'https://www.baidu.com'
        conn = requests.get(url, proxies=proxy, timeout=3.0, headers=headers)
        html_doc = conn.text
        if html_doc.find(u'百度一下，你就知道') > 0:
            print(data +" ok")
            ip_client.insert(data)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    client = pymongo.MongoClient('localhost', 27017)
    db = client['local']
    ip_client = db['ips']
    #datas=getIps()
    datas=[]
    inFile = open('proxy.txt', 'r')
    while True:
        line = inFile.readline().strip()
        if len(line) == 0: break
        protocol, proxy = line.split('=')
        data={}
        data['protocol']=protocol
        data['ip']=proxy
        datas.append(data)
        if(len(datas)%100):
            print(" "+str(len(datas)))

    print('test begin')
    tasks = [gevent.spawn(test, data,ip_client) for data in datas]
    gevent.joinall(tasks)



def isOk(ip):
    proxy = {'http': 'http://' + ip}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    url = 'https://www.baidu.com'
    try:
        conn = requests.get(url, proxies=proxy, timeout=3.0, headers=headers)
        conn.encoding = 'utf-8'
        html_doc = conn.text
        if html_doc.find(u'百度一下，你就知道') > 0:
            return True
    except Exception as e:
        print(e)
        pass
import requests
import json
import re
import time
import random
import hashlib
import os

name = '381078SX007'        # 一评账号
otherUser = '381078SX030'   # 二评账号

qName = '24'                # 试题在页面显示的第几题

pwd = '123'                 # 帐号密码



url = 'http://xyyj.jsleascent.com'

# host = '47.97.153.241:9095'#服务器地址
class OnlineMark(object):
    """docstring for OnlineMark"""
    def __init__(self, user, pwd, host):
        super(OnlineMark, self).__init__()
        self.user = user
        self.pwd = pwd
        self.lessonID = ''  # 课程ID
        self.qId = ''       # 试题ID
        self.s = requests.Session()
        self.hostIP = host  # '47.97.153.241:9095' 服务器地址
        self.hostURL = 'http://'+host+'/'

    def login(self):
        name = self.user
        # pwd = self.pwd

        m = hashlib.md5()
        m.update(self.pwd.encode('utf-8'))
        m.hexdigest()
        pwd = m.hexdigest()

        hostURL = self.hostURL
        hostIP = self.hostIP
        url = hostURL + 'account/Logon'
        h = {
            'Host': hostIP,
            'Accept': 'text/html, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': hostURL[:-1],
            'Referer': hostURL,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }
        data = f'UserID={name}&UserPW={pwd}'
        f = self.s.post(url,data=data,headers=h)

        p1 = {
            'Host': hostIP,
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        f = self.s.get(hostURL, headers = p1)
        self.hostIP = re.search('http://(.+?)/', f.url).group(1)
        self.hostURL = f.url
        # print(self.hostIP)
        # exit()

        PaperList = re.search('PaperList = (\[.+?\])', f.text).group(1)
        # print(PaperList)
        PaperList = PaperList.replace('true', 'True')
        PaperList = PaperList.replace('false', 'False')
        for item in eval(PaperList):
            # print(item)
            # item = json.loads(item)
            # 试卷ID号 语数英的ID
            TestID2 = item['TestID']
            # 试题ID  试卷的顺序号
            qId2 = item['QuesID']
            # 试题在页面显示的名称
            qName2 = item['QuesName']
            # "MCaption":"7.1?7.2" 表示有7(1)和7(2)要批改
            mCaption2 = item['MCaption']
            # print(TestID2, qId2, qName2)
            # roleID2 = item['RoleID']
            if qName == qName2:
                TestID = str(TestID2)
                qId = str(qId2)
                # print(TestID, qId, qName)
                return TestID, qId



    def logout(self):
        name = self.user
        hostURL = f'http://{self.hostIP}/'
        hostIP = self.hostIP
        # print(hostIP)
        # exit()
        url = hostURL + 'account/logout'
        header = {
            'Host': hostIP,
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': hostURL[:-1] + ':9090',
            'Referer': hostURL + 'home/index',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        f = self.s.post(url,data=None,headers=header)
        if 'logout' in f.text:
            print(f'退出账号成功:{name}')

    def getPaper(self, lessonID, quesID):
        hostURL = self.hostURL
        hostIP = self.hostIP        

        paper = []
        paperDic = {}
        url = f'http://{hostIP}/home/GetUserHistoryMark'
        header = {
            'Host': hostIP,
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': hostURL[:-1],
            'Referer': hostURL + 'home/index',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9  ' ,
        }
        data = 'TestID='+lessonID+'&questionId='+quesID+'&mark=&wrid=0&orderType=0&orderDirection=0&arb=0'
        f = self.s.post(url,data=data,headers=header)
        print(f.text)
        result = f.json()
        for i in result:
            paper.append(i)
        # 获取该页的最后试题ID
        try:
            WRID = paper[-1]['WRID']
        except:
            print(f'该账号没有批改该题：{qName}')
            exit()
        while True:
            # sign = WRID
            data = 'TestID='+lessonID+'&questionId='+quesID+'&mark=&wrid='+str(WRID)+'&orderType=0&orderDirection=0&arb=0'
            f = self.s.post(url,data=data,headers=header)
            # print(f.json())
            result = f.json()
            if result == []:
                break
            for i in result:
                paper.append(i)
            WRID = paper[-1]['WRID']


        # print(paper)
        # print('++++++++++++++')
        for i in paper:
            paperId = i['PaperId']
            rowId = str(i['RowID'])
            mark = i['MarkScore']
            SmallQuesMark = i['SmallQuesMark']
            paperDic[paperId] = {'RowID':rowId, 'SmallQuesMark':SmallQuesMark, 'Mark':mark}
        print('共提取试卷份数：', len(paperDic))
        # print('+++++++++')
        return paperDic


    def getQuestion(self, lessonID, quesID, dic):
        hostURL = f'http://{self.hostIP}/'
        hostIP = self.hostIP
        header = {
            'Host': hostIP,
            'Connection': 'keep-alive',
            'Accept': 'text/html, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': hostURL[:-1],
            'Referer': hostURL + 'home/index',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }
        i = 0
        while True:
            url = hostURL + 'home/GetQuestion'
            data = f'testId={lessonID}&questionId={quesID}&count=3&lidPre=2&qidPre=3&refresh=0&arb=0&QOControlInfo=0&MySetting=0&ImgHandler=2'
            f = self.s.post(url,data=data,headers=header)
            res = f.json()
            # print(res)
            if len(res) == 0:
                print('刷新任务...')
                i += 1
                time.sleep(3)
                if i == 3:
                    print('本次任务已完成！')
                    break
                else:
                    continue
            for item in res:
                # print(item)
                rowId = item['RowID']
                paperId = item['PaperId']
                bwId = item['BWRID']

                url = hostURL + 'home/SetMark'
                rnd = str(random.randint(1000,3000))
                try:
                    mark = int(dic[paperId]['Mark'].split('.')[0])
                except:
                    mark = 0
                data = f'testId={lessonID}&questionId={quesID}&paperId={paperId}&score={str((mark))}&bwId={bwId}&rowId={rowId}&markType=0&needReleaseNum=2&gfNum=0&elapsedTime={rnd}&sAnns=&flag=0&arb=0&ysf=%22%22&isdebug=0'
                #        testId=6&questionId=4&paperId=XY2582_22123923_02B&score=6&bwId=1216368&rowId=1298&markType=0&needReleaseNum=2&gfNum=0&elapsedTime=26513&sAnns=&flag=0&arb=0&ysf=%22%22&isdebug=0
                f = self.s.post(url,data=data,headers=header)
                print(f.text)
                time.sleep(int(rnd)/1000)

def getHost(url, matchString):
    res = requests.get(url)
    res.encoding = 'gb2312'
    # print(res.text)
    pattern = re.compile(f'href="http://(.+?)">.+%s'%matchString)
    # print(pattern)
    h = pattern.search(res.text).group(1)
    if '/' in h:
        h = h[:-1]
    return h


matchString = '8数'
host = getHost(url, matchString)
# print(host)
# exit()
if not os.path.exists(f"{name}.json"):
    OnMark = OnlineMark(name, pwd, host)
    lessonID, quesID = OnMark.login()
    print(lessonID, quesID)
    dic = OnMark.getPaper(lessonID, quesID)
    OnMark.logout()
    # print(dic)
    with open(f"{name}.json", "w") as outfile:
            json.dump(dic, outfile)

# 读取本地 JSON 文件
with open(f"{name}.json", "r") as infile:
    data = json.load(infile)
# print(data)
# exit()
OtherMark = OnlineMark(otherUser, pwd, host)
lessonID, quesID = OtherMark.login()
OtherMark.getQuestion(lessonID, quesID, data)
OtherMark.logout()
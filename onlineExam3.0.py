import requests
import json
import re
import time
import random
import hashlib
import os
from urllib.parse import quote 

Accounts = [
    '381079SX005']          # 一评账号
otherUser = '381079SX009'   # 二评账号
pwd = '123'                 # 帐号密码

qName = '20'                # 试题在页面显示的第几题

# matchString = '初三数学'


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
        # 去掉结尾空格
        # hostURL = "http://115.29.243.122:8088/"
        hostIP = self.hostIP
        url = hostURL + 'account/Logon'
        # print(url)
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
        if f.json()['Text'] == '用户名不存在':
            return False
            exit()
        else:
            print('登录成功')
            return True
        
    def getTestID(self):
        hostIP = self.hostIP
        hostURL = self.hostURL  
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
        return None, None



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
            data = f'testId={lessonID}&questionId={quesID}&count=3&lidPre=2&qidPre=6&refresh=0&arb=0&QOControlInfo=0&MySetting=0&ImgHandler=2'
            f = self.s.post(url,data=data,headers=header, allow_redirects=False)
            res = f.json()
            # print(res)
            if len(res) == 0:
                print('刷新任务...')
                # exit()
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
                # print(f'rowId:{rowId},paperId:{paperId},bwId:{bwId}')
                url = hostURL + 'home/SetMark'
                rnd = str(random.randint(1000,4000) * 3)
                try:
                    mark = quote(dic[paperId]['SmallQuesMark'])
                except:
                    # 没有获取该题的得分，则跳过
                    print('没有获取该题的得分')
                    continue
                data = f'testId={lessonID}&questionId={quesID}&paperId={paperId}&score={str((mark))}&bwId={bwId}&rowId={rowId}&markType=0&needReleaseNum=2&gfNum=0&elapsedTime={rnd}&sAnns=&flag=0&arb=0&ysf=%22%22&isdebug=0'
                #        testId=2&questionId=1&paperId=XY1082_14131641_01A&score=4%2C4%2C4%2C4%2C4%2C4%2C4%2C4&bwId=1282996&rowId=234217&markType=0&needReleaseNum=2&gfNum=0&elapsedTime=336044&sAnns=&flag=0&arb=0&ysf=%22%22&isdebug=0
                f = self.s.post(url,data=data,headers=header)
                print(f.text)
                time.sleep(random.randint(1000,3000)/1000)

            # exit()




def getHost(url):
    """
    返回阅卷地址列表。
    """
    res = requests.get(url)   
    # print(res.text)
    url_pattern =  r'(?<=href="http://)[\d.]+:\d+(?=\s*/?\s*")'
    urls = re.findall(url_pattern, res.text)
    return urls
    # print(urls)
    # exit()
    # try:
    #     pattern = re.compile(f'href="http://(.+?)">.+%s'%matchString)
    #     # print(pattern)
    #     h = pattern.search(res.text).group(1)
    # except AttributeError:
    #     raise Exception('未找到匹配的host')
    # if '/' in h:
    #     h = h[:-1]
    # exit()
    # return h
    




from typing import List, Dict, Callable, Any

def read_json_files(file_names: List[str]) -> List[Dict[str, Any]]:
    """
    读取多个 JSON 文件并返回它们的内容列表。
    
    Args:
        file_names: JSON 文件名列表
        
    Returns:
        List[Dict[str, Any]]: 包含每个 JSON 文件内容的字典列表
    """
    data_list = []
    for file_name in file_names:
        file_name = file_name + '.json'
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_list.append(data)
        except FileNotFoundError:
            print(f"警告: 文件 {file_name} 未找到，跳过")
        except json.JSONDecodeError as e:
            print(f"警告: 文件 {file_name} 不是有效的 JSON 格式，跳过。错误: {e}")
    return data_list

def merge_json_files(file_names: List[str], output_file: str, merge_func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]] = None) -> None:
    """
    读取多个 JSON 文件并合并它们的内容到一个新的 JSON 文件。
    
    Args:
        file_names: JSON 文件名列表
        output_file: 输出文件名
        merge_func: 合并函数，默认为简单的字典合并，后面的 JSON 文件会覆盖前面的同名键
    """
    # 读取所有 JSON 文件
    data_list = read_json_files(file_names)
    
    # 如果没有数据，直接返回
    if not data_list:
        print("没有有效的 JSON 数据可以合并")
        return
    
    # 如果没有提供自定义合并函数，使用默认的字典合并
    if merge_func is None:
        # 初始化合并数据为第一个 JSON 文件的数据
        merged_data = data_list[0].copy()
        # 逐个合并后续的 JSON 文件数据
        for data in data_list[1:]:
            merged_data.update(data)
    else:
        # 使用自定义合并函数
        merged_data = data_list[0].copy()
        for data in data_list[1:]:
            merged_data = merge_func(merged_data, data)
    
    # 写入合并后的数据到新的 JSON 文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
        print(f"已将 JSON 数据合并到 {output_file}")
    except IOError as e:
        print(f"写入文件 {output_file} 时出错: {e}")


if __name__ == '__main__':
    AllHost = getHost(url)
    # print(AllHost)
    host = ''
    for name in Accounts:
        # print(name)
        if not os.path.exists(f"{name}.json"):
            for h in AllHost:
                OnMark = OnlineMark(name, pwd, h)
                if OnMark.login():
                    host = h
                    lessonID, quesID = OnMark.getTestID()
                    break
                else:
                    time.sleep(1.5)
            if lessonID:
                print(f'"TestID":{lessonID},"QuesID":{quesID}')
                dic = OnMark.getPaper(lessonID, quesID)
                OnMark.logout()
                # print(dic)
                with open(f"{name}.json", "w") as outfile:
                        json.dump(dic, outfile)
            else:
                print('没有这个题号！')
                exit()

    dataFile = Accounts[0][6:8] + qName
    if len(Accounts) > 1:
        if not os.path.exists(f"{dataFile}.json"):
            merge_json_files(Accounts, dataFile + '.json')
    else:
        dataFile = Accounts[0]

    # 读取本地 JSON 文件（一评数据）
    with open(f"{dataFile}.json", "r") as infile:
        data = json.load(infile)
    # print(data)
    # exit()

    if  host == '':
        for h in AllHost:
                OtherMark = OnlineMark(otherUser, pwd, h)
                if OtherMark.login():
                    host = h
                    lessonID, quesID = OtherMark.getTestID()
                    OtherMark.getQuestion(lessonID, quesID, data)
                    break
                else:
                    time.sleep(1.5)
    else:
        OtherMark = OnlineMark(otherUser, pwd, host)
        if OtherMark.login():
            lessonID, quesID = OtherMark.getTestID()
        OtherMark.getQuestion(lessonID, quesID, data)
    OtherMark.logout()
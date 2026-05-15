"""网上阅卷核心类 - 改造为支持多用户并发操作"""
import requests
import re
import time
import random
import hashlib
import json
from urllib.parse import quote


class OnlineMark:
    """网上阅卷操作类，每个实例独立session，支持并发"""

    def __init__(self, user, pwd, host, log_callback=None):
        self.user = user
        self.pwd = pwd
        self.lessonID = ''
        self.qId = ''
        self.s = requests.Session()
        self.hostIP = host
        self.hostURL = 'http://' + host + '/'
        self.log_callback = log_callback  # 日志回调函数
        self._stopped = False  # 停止标志

    def _log(self, msg):
        """输出日志"""
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    def stop(self):
        """请求停止当前任务"""
        self._stopped = True

    def login(self):
        name = self.user
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
        f = self.s.post(url, data=data, headers=h)
        result = f.json()
        if result.get('Text') == '用户名不存在':
            self._log(f'账号 {name} 登录失败: 用户名不存在')
            return False
        if result.get('Text') == '登录密码不正确':
            self._log(f'账号 {name} 登录失败: 密码错误')
            return False
        else:
            self._log(f'账号 {name} 登录成功')
            return True

    def getTestID(self, qName):
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
        f = self.s.get(hostURL, headers=p1)

        # 提取hostIP
        match = re.search('http://(.+?)/', f.url)
        if not match:
            self._log('无法从响应URL中提取服务器地址')
            return None, None
        self.hostIP = match.group(1)
        self.hostURL = f.url

        # 提取PaperList
        match = re.search(r'PaperList = (\[.+?\])', f.text)
        if not match:
            self._log('无法从页面中提取试卷列表')
            return None, None
        PaperList = match.group(1)
        PaperList = PaperList.replace('true', 'True')
        PaperList = PaperList.replace('false', 'False')
        for item in eval(PaperList):
            TestID2 = item['TestID']
            qId2 = item['QuesID']
            qName2 = item['QuesName']
            mCaption2 = item['MCaption']
            if qName == qName2:
                TestID = str(TestID2)
                qId = str(qId2)
                self._log(f'找到试题: TestID={TestID}, QuesID={qId}, 名称={qName}')
                return TestID, qId
        self._log(f'未找到试题: {qName}')
        return None, None

    def logout(self):
        name = self.user
        hostURL = f'http://{self.hostIP}/'
        hostIP = self.hostIP
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
        f = self.s.post(url, data=None, headers=header)
        if 'logout' in f.text:
            self._log(f'退出账号成功: {name}')

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
            'Accept-Language': 'zh-CN,zh;q=0.9  ',
        }
        data = 'TestID=' + lessonID + '&questionId=' + quesID + '&mark=&wrid=0&orderType=0&orderDirection=0&arb=0'
        f = self.s.post(url, data=data, headers=header)
        result = f.json()
        for i in result:
            paper.append(i)
        try:
            WRID = paper[-1]['WRID']
        except (IndexError, KeyError):
            self._log('该账号没有批改该题')
            return {}

        while True:
            if self._stopped:
                self._log('任务已停止')
                return {}
            data = 'TestID=' + lessonID + '&questionId=' + quesID + '&mark=&wrid=' + str(WRID) + '&orderType=0&orderDirection=0&arb=0'
            f = self.s.post(url, data=data, headers=header)
            result = f.json()
            if result == []:
                break
            for i in result:
                paper.append(i)
            WRID = paper[-1]['WRID']

        for i in paper:
            paperId = i['PaperId']
            rowId = str(i['RowID'])
            mark = i['MarkScore']
            SmallQuesMark = i['SmallQuesMark']
            paperDic[paperId] = {'RowID': rowId, 'SmallQuesMark': SmallQuesMark, 'Mark': mark}
        self._log(f'共提取试卷份数: {len(paperDic)}')
        return paperDic

    def getProgress(self, lessonID, quesID):
        """通过 GetPersonWorkNumInfo 获取批改进度

        Args:
            lessonID: 课程ID (TestID)
            quesID: 试题ID (questionId)

        Returns:
            dict: {'total': 总数, 'marked': 已批改数} 或 None
        """
        hostURL = f'http://{self.hostIP}/'
        hostIP = self.hostIP
        url = hostURL + 'home/GetPersonWorkNumInfo'
        header = {
            'Host': hostIP,
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': hostURL[:-1],
            'Referer': hostURL + 'home/index',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        data = f'TestID={lessonID}&questionId={quesID}'
        try:
            f = self.s.post(url, data=data, headers=header)
            result = f.json()
            sum_info = result.get('Sum', [{}])[0] if result.get('Sum') else {}
            total = sum_info.get('TotalNum', 0)
            marked = sum_info.get('MarkedNum', 0)
            return {'total': total, 'marked': marked}
        except Exception as e:
            self._log(f'获取进度失败: {e}')
            return None

    def getQuestion(self, lessonID, quesID, dic, progress_callback=None, progress_api_callback=None, refresh_delay=3):
        """提交评分，支持进度回调和停止控制

        Args:
            lessonID: 课程ID
            quesID: 试题ID
            dic: 评分数据字典
            progress_callback: 进度回调函数 callback(marked)
            progress_api_callback: API进度回调函数 callback(lessonID, quesID)
            refresh_delay: 提交数据时的延迟时间（秒），默认3秒
        """
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
        total_marked = 0
        while True:
            if self._stopped:
                self._log('任务已停止')
                break
            url = hostURL + 'home/GetQuestion'
            data = f'testId={lessonID}&questionId={quesID}&count=3&lidPre=2&qidPre=6&refresh=0&arb=0&QOControlInfo=0&MySetting=0&ImgHandler=2'
            f = self.s.post(url, data=data, headers=header, allow_redirects=False)
            if f.status_code != 200:
                self._log(f'GetQuestion请求失败: HTTP {f.status_code}')
                i += 1
                time.sleep(refresh_delay + i)
                continue
            res = f.json()
            if len(res) == 0:
                if progress_api_callback:
                    progress_api_callback(lessonID, quesID)
                progress = self.getProgress(lessonID, quesID)
                if progress and progress.get('total', 0) > 0 and progress['marked'] >= progress['total']:
                    self._log(f'任务已完成: {progress["marked"]}/{progress["total"]}')
                    break
                i += 1
                self._log(f'暂无新试卷，等待 {refresh_delay + i} 秒...')
                time.sleep(refresh_delay + i)
                continue
            i = 0
            for item in res:
                if self._stopped:
                    self._log('任务已停止')
                    break
                rowId = item['RowID']
                paperId = item['PaperId']
                bwId = item['BWRID']
                url = hostURL + 'home/SetMark'
                rnd = str(random.randint(1000, 4000) * 3)
                try:
                    mark = quote(dic[paperId]['SmallQuesMark'])
                except KeyError:
                    self._log(f'没有获取该题的得分: {paperId}')
                    continue
                data = f'testId={lessonID}&questionId={quesID}&paperId={paperId}&score={str(mark)}&bwId={bwId}&rowId={rowId}&markType=0&needReleaseNum=2&gfNum=0&elapsedTime={rnd}&sAnns=&flag=0&arb=0&ysf=%22%22&isdebug=0'
                f = self.s.post(url, data=data, headers=header)
                self._log(f'提交评分: {paperId} -> {f.text}')
                # 从响应的Data字段解析已批改数量，格式如: {"Msg":"提交成功","Code":0,"Data":"93|234","Total":0}
                try:
                    resp_json = f.json()
                    data_field = resp_json.get('Data', '')
                    if data_field and '|' in data_field:
                        total_marked = int(data_field.split('|')[0])
                    else:
                        total_marked += 1
                except (ValueError, KeyError, IndexError):
                    total_marked += 1
                if progress_callback:
                    progress_callback(total_marked)
                if progress_api_callback:
                    progress_api_callback(lessonID, quesID)
                time.sleep(random.uniform(2, refresh_delay))



def getHost(url):
    """返回阅卷地址列表，排除HTML注释中的链接"""
    res = requests.get(url)
    text = res.text
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    url_pattern = r'(?<=href="http://)[\d.]+:\d+(?=\s*/?\s*")'
    urls = re.findall(url_pattern, text)
    return urls


def merge_paper_data(data_list):
    """合并多个一评账号的试卷数据"""
    merged = {}
    for data in data_list:
        merged.update(data)
    return merged



'''
POST http://118.178.170.16:9090/home/QuesProgress HTTP/1.1
Host: 118.178.170.16:9090
Proxy-Connection: keep-alive
Content-Length: 22
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
Origin: http://118.178.170.16:9090
Content-Type: application/x-www-form-urlencoded
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://118.178.170.16:9090/home/index
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: ASP.NET_SessionId=oletxk5jccfoyuytvxkepfxe

TestID=3&QuesID=9&ur=0

'''
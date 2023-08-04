import re
import json
import requests
import urllib.parse
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
##################################################################
from Utils import Utils
import traceback
#################################################################
class sessions(requests.Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout',10)
        return super(sessions, self).request(*args, **kwargs)                    
class Login:
    # 初始化登陆模块
    def __init__(self,user,School):
        self.session =sessions()  
        headers = {
            'User-Agent':
            'Mozilla/5.0 (Linux; Android 8.0.0; MI 6 Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 okhttp/3.12.4'}
        self.session.headers = headers
        self.headers = {
            'User-Agent':
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
            'Content-Type': 'application/x-www-form-urlencoded'}
        self.username = user['username'];self.password = user['password']
        self.school = user['school'];self.address=user.get('address','');self.id=user.get('id','')
        self.login_url = School['login_url']
        self.host = School['login_host']
        self.type = School['login_type']
        self.campus_host =School['campus_host']
        self.Trytimes =0
        self.count = 0
        
    def getCookie(self):
        while self.Trytimes<3:
            self.Trytimes+=1;flag=True
            print(f"账号{self.username}正在尝试第{self.Trytimes}次登录")
            try:
                self.session.cookies=self.iaplogin() if self.type == 'CLOUD' else self.caslogin()
                headers =  {'User-Agent': 'Mozilla/5.0 (Linux; Android 12; 22021211RC Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046125 Mobile Safari/537.36 wxwork/4.0.19 MicroMessenger/7.0.1 NetType/WIFI Language/zh Lang/zh ColorScheme/Light',
                'Content-Type':'application/json;charset=UTF-8'}
                res=self.session.post(self.campus_host+'wec-counselor-sign-apps/stu/sign/getStuSignInfosInOneDay', headers=headers,data=json.dumps({}), verify=False)
                if res.status_code!=418:
                    Utils.log(f"账号{self.username}登录成功");return True
                print('ip被拦截');break
            except Exception as e:
                flag=False
                print(f'[{e}]\n{traceback.format_exc()}')
        if not flag:       
            Utils.log(f"账号:{self.username} 密码:{self.password} 可能有误,请自行前往: {self.login_url} 校验账号密码正确性"); return False
        Utils.log(f"账号:{self.username}登录失败")  
    def iaplogin(self):
        params = {}
        self.ltInfo = self.session.post(f'{self.host}iap/security/lt',
                                        data=json.dumps({})).json()
        params['lt'] = self.ltInfo['result']['_lt']
        params['rememberMe'] = 'false'
        params['dllt'] = ''
        params['mobile'] = ''
        params['username'] = self.username
        params['password'] = self.password
        needCaptcha  = self.session.post(f'{self.host}iap/checkNeedCaptcha?username={self.username}',data=json.dumps({}),verify=False).json()['needCaptcha']
        if needCaptcha:
            imgUrl = f'{self.host}iap/generateCaptcha?ltId={self.ltInfo["result"]["_lt"]}'
            code = Utils.getCodeFromImg(self.session, imgUrl)
            params['captcha'] = code
        else:
            params['captcha'] = ''
        data = self.session.post(f'{ self.host }iap/doLogin',
                                 params=params,
                                 verify=False,
                                 allow_redirects=False)
        if data.status_code == 302:
            data = self.session.post(data.headers['Location'], verify=False)
            return self.session.cookies
        else:
            data = data.json()
            self.count += 1
            if data['resultCode'] == 'CAPTCHA_NOTMATCH':
                if self.count < 10:
                    self.login()
                else:
                    raise Exception('验证码错误超过10次，请检查')
            elif data['resultCode'] == 'FAIL_UPNOTMATCH':
                raise Exception('用户名密码不匹配，请检查')
            else:
                raise Exception(f'登陆出错，状态码：{ data["resultCode"]}，请联系开发者修复...')
    def getNeedCaptchaUrl(self):
        if self.type == 0:
            url = self.host + 'authserver/needCaptcha.html' + '?username=' + self.username
            flag = self.session.get(url, verify=False).text
            return 'false' != flag[:5] and 'False' != flag[:5]
        else:
            url = self.host + 'authserver/checkNeedCaptcha.htl' + '?username=' + self.username
            flag = self.session.get(url, verify=False).json()
            return flag['isNeed']
    def caslogin(self):
        html = self.session.get(self.login_url, verify=False).text
        soup = BeautifulSoup(html, 'html.parser')
        if len(soup.select('#casLoginForm')) > 0:
            self.type = 0
        elif len(soup.select('#loginFromId')) > 0:
            soup = BeautifulSoup(str(soup.select('#loginFromId')[1]), 'html.parser')
            self.type = 1
        elif len(soup.select('#fm1')) > 0:
            soup = BeautifulSoup(str(soup.select('#fm1')[0]), 'html.parser')
            self.type = 2
        else:
            raise Exception('登录IP被拦截!')
        params = {}
        form = soup.select('input')
        for item in form:
            if None != item.get('name') and len(item.get('name')) > 0:
                if item.get('name') != 'rememberMe':
                    if None == item.get('value'):
                        params[item.get('name')] = ''
                    else:
                        params[item.get('name')] = item.get('value')
        params['username'] = self.username
        if self.type == 2:
            pattern = 'RSAKeyPair\((.*?)\);'
            publicKey = re.findall(pattern, html)
            publicKey = publicKey[0].replace('"', "").split(',')
            params['password'] = Utils.encryptRSA(self.password, publicKey[2],
                                                  publicKey[0])
            params['captcha'] = Utils.getCodeFromImg(
                self.session, self.host + 'lyuapServer/captcha.jsp')
        else:
            if self.type == 0:
                salt = soup.select("#pwdDefaultEncryptSalt")
            else:
                salt = soup.select("#pwdEncryptSalt")
            if len(salt) != 0:
                salt = salt[0].get('value')
            else:
                pattern = '\"(\w{16})\"'
                salt = re.findall(pattern, html)
                if len(salt) == 1:
                    salt = salt[0]
                else:
                    salt = False
            if not salt:
                params['password'] = self.password
            else:
                params['password'] = Utils.encryptAES(
                    Utils.randString(64) + self.password, salt)
            if self.getNeedCaptchaUrl():
                if self.type == 0:
                    imgUrl = self.host + 'authserver/captcha.html'
                    params['captchaResponse'] = Utils.getCodeFromImg(
                        self.session, imgUrl)
                else:
                    imgUrl = self.host + 'authserver/getCaptcha.htl'
                    params['captcha'] = Utils.getCodeFromImg(
                        self.session, imgUrl)
        data = self.session.post(self.login_url,
                                 data=urllib.parse.urlencode(params),
                                 headers=self.headers,
                                 allow_redirects=False)
        # 如果等于302强制跳转，代表登陆成功
        if data.status_code == 302:
            jump_url = data.headers['Location']
            res = self.session.post(jump_url, verify=False)
            if res.url.find('campusphere.net/') == -1:
                raise Exception('CAS登陆失败,未能成功跳转今日校园!')
            return self.session.cookies
        elif data.status_code == 200 or data.status_code == 401:
            data = data.text
            soup = BeautifulSoup(data, 'html.parser')
            if len(soup.select('#errorMsg')) > 0:
                msg = soup.select('#errorMsg')[0].get_text()
            elif len(soup.select('#formErrorTip2')) > 0:
                msg = soup.select('#formErrorTip2')[0].get_text()
            elif len(soup.select('#msg')) > 0:
                msg = soup.select('#msg')[0].get_text()
            else:
                msg = 'CAS登陆失败,意料之外的错误!'
            raise Exception(msg)
        else:
            raise Exception('CAS登陆失败！返回状态码：' + str(data.status_code))               
import base64
import json
import random
import rsa
import requests
import sys
import time
from Crypto.Cipher import AES
from datetime import datetime, timedelta, timezone
from requests_toolbelt import MultipartEncoder
import os
from pyDes import des, CBC, PAD_PKCS5
import re
import hashlib
import urllib.parse
from urllib.parse import urlparse
import traceback
from io import BytesIO
          
###############################################
class Utils:
    logs=''
    def __init__(self):
        pass
    @staticmethod
    def getCodeFromImg(res,imgurl):
        import muggle_ocr
        sdk = muggle_ocr.SDK(model_type = muggle_ocr.ModelType.Captcha)
        Captcha=res.get(url=imgurl)
        imgcode=sdk.predict(image_bytes = Captcha.content)
        print(imgcode)
        return imgcode
#*************************Aes加密*************************************#
    @staticmethod
    def randString(length):
        baseString = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
        data = ''
        for i in range(length):
            data += baseString[random.randint(0, len(baseString) - 1)]
        return data
    @staticmethod    
    def encryptAES(data, key):
        ivStr = '\x01\x02\x03\x04\x05\x06\x07\x08\x09\x01\x02\x03\x04\x05\x06\x07'
        aes = AES.new(bytes(key, encoding='utf-8'), AES.MODE_CBC,bytes(ivStr, encoding="utf8"))
        text_length = len(data)
        amount_to_pad = AES.block_size - (text_length % AES.block_size)
        if amount_to_pad == 0:
            amount_to_pad = AES.block_size
        pad = chr(amount_to_pad)
        data = data + pad * amount_to_pad
        text = aes.encrypt(bytes(data, encoding='utf-8'))
        text = base64.encodebytes(text)
        text = text.decode('utf-8').strip()
        return text                       
#*************************RSA加密*******************************#
    @staticmethod
    def encryptRSA(message, m, e):
            mm = int(m, 16)
            ee = int(e, 16)
            rsa_pubkey = rsa.PublicKey(mm, ee)
            crypto = Utils._encrypt_rsa(message.encode(), rsa_pubkey)
            return crypto.hex()
    @staticmethod        
    def _encrypt_rsa(message, pub_key):
            keylength = rsa.common.byte_size(pub_key.n)
            padded = Utils._pad_for_encryption_rsa(message, keylength)
            payload = rsa.transform.bytes2int(padded)
            encrypted = rsa.core.encrypt_int(payload, pub_key.e, pub_key.n)
            block = rsa.transform.int2bytes(encrypted, keylength)
            return block
    @staticmethod        
    def _pad_for_encryption_rsa(message, target_length):
            message = message[::-1]
            max_msglength = target_length - 11
            msglength = len(message)
            padding = b''
            padding_length = target_length - msglength - 3
            for i in range(padding_length):
                padding += b'\x00'
            return b''.join([b'\x00\x00', padding, b'\x00', message])                            
#*******************************表单加密***************************#
    @staticmethod
    def log(content, show=True):
        Text = Utils.getTime() + ' ' + str(content)
        if show:
            print(Text)
        if Utils.logs:
            Utils.logs = Utils.logs+'<br>'+Text
        else:
            Utils.logs = Text
        sys.stdout.flush()
    @staticmethod
    def getTime(Mod='%Y-%m-%d %H:%M:%S', offset=0):
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        bj_dt = bj_dt-timedelta(days=offset)
        return bj_dt.strftime(Mod)
    @staticmethod
    def DESEncrypt(s, key='XCE927=='):
        key = key
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(s)
        return base64.b64encode(encrypt_str).decode()

    @staticmethod
    def md5(str):
        md5 = hashlib.md5()
        md5.update(str.encode("utf8"))
        return md5.hexdigest()

    @staticmethod    
    def GenDeviceID(username):
        deviceId = ''
        random.seed(username.encode('utf-8'))
        for i in range(8):
            num = random.randint(97, 122)
            if (num*i+random.randint(1, 8)) % 3 == 0:
                deviceId = deviceId+str(num % 9)
            else:
                deviceId = deviceId+chr(num)
        deviceId = deviceId+'Iphone13ProMax'
        return deviceId
    @staticmethod
    def submitFormData(env):
        deviceId= env.userInfo['id'] if env.userInfo['id'] else Utils.GenDeviceID(env.userInfo['username'])
        extension = {
            "lon": env.userInfo['longitude'],
            "model": "Iphone13ProMax",
            "appVersion": "9.0.12",
            "systemVersion": "8.0.0",
            "userId": env.userInfo['username'],"appVersion": "9.0.20",
            "systemName": "Ios",
            "lat": env.userInfo['latitude'],
            "deviceId": deviceId
        }
        headers = {
            'User-Agent':
            'Mozilla/5.0 (Linux; Ios 15.0.0; Iphone13ProMax Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 okhttp/3.12.4 cpdaily/9.0.20 wisedu/9.0.20',
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': Utils.DESEncrypt(json.dumps(extension)),
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Encoding': 'gzip',
            'Host': re.findall('//(.*?)/', env.host)[0],
            'Connection': 'Keep-Alive'
        }
        bodyString = Utils.encryptAES(
            json.dumps(env.submitData), 'SASEoK4Pa5d4SssO')
        env.submitData['bodyString'] = bodyString
        formData = {
            'version':
            'first_v3',
            'calVersion':
            'firstv',
            'bodyString': bodyString,
            'sign': Utils.md5(urllib.parse.urlencode(env.submitData) + "&SASEoK4Pa5d4SssO")
        }
        formData.update(extension)
        return env.session.post(env.host + env.submitApi,headers=headers,data=json.dumps(formData),verify=False)
#*****************************图片上传**************************#
# 上传图片到阿里云oss
    @staticmethod
    def uploadPicture(env, api, picSrc):
        url = env.host + api
        res = env.session.post(url=url,
                               headers={'content-type': 'application/json'},
                               data=json.dumps({'fileType': 1}),
                               verify=False)
        datas = res.json().get('datas')
        fileName = datas.get('fileName')
        policy = datas.get('policy')
        accessKeyId = datas.get('accessid')
        signature = datas.get('signature')
        policyHost = datas.get('host')
        headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'
        }
        multipart_encoder = MultipartEncoder(
            fields={  # 这里根据需要进行参数格式设置
                'key': fileName, 'policy': policy, 'AccessKeyId': accessKeyId, 'signature': signature, 'x-obs-acl': 'public-read',
                'file': ('blob', open(os.path.join(os.path.dirname(__file__), '../', picSrc), 'rb'), 'image/jpg')
            })
        headers['Content-Type'] = multipart_encoder.content_type
        env.session.post(url=policyHost,
                         headers=headers,
                         data=multipart_encoder)
        env.fileName = fileName

    # 获取图片上传位置
    @staticmethod
    def getPictureUrl(env, api):
        url = env.host + api
        params = {'ossKey': env.fileName}
        res = env.session.post(url=url,
                               headers={'content-type': 'application/json'},
                               data=json.dumps(params),
                               verify=False)
        photoUrl = res.json().get('datas')
        return photoUrl
#**********************获取学校信息****************************#
    def get_school(schoolName):
        Utils.log(f"开始获取{schoolName}的登录信息")
        session=requests.session()
        headers = {'User-Agent':'Mozilla/5.0 (Linux; Android 8.0.0; MI 6 Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 okhttp/3.12.4',}
        session.headers = headers
        schools = session.get('https://mobile.campushoy.com/v6/config/guest/tenant/list', verify=False).json()['data']
        for item in schools:
            if item['name'] == schoolName:
                if item['joinType'] == 'NONE':
                    raise Exception(schoolName + '未加入今日校园，请检查...')
                params = {'ids': item['id']}
                data = session.get('https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params,verify=False, ).json()['data'][0]
                login_type= data['joinType']
                idsUrl = data['idsUrl']
                ampUrl = data['ampUrl']
                if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                    campus_host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl)[0]
                    status_code = 0
                    while status_code != 200:
                        newAmpUrl = session.get(ampUrl, allow_redirects=False, verify=False)
                        status_code = newAmpUrl.status_code
                        if 'Location' in newAmpUrl.headers:
                            ampUrl = newAmpUrl.headers['Location']
                    parse = urlparse(ampUrl)
                    host = parse.netloc
                    login_url = ampUrl
                    login_host = re.findall('\w{4,5}\:\/\/.*?\/', login_url)[0]
                ampUrl2 = data['ampUrl2']
                if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                    campus_host = re.findall('\w{4,5}\:\/\/.*?\/', ampUrl2)[0]
                    parse = urlparse(ampUrl2)
                    host = parse.netloc
                    res = session.get(parse.scheme + '://' + host)
                    parse = urlparse(res.url)
                    login_url = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                    login_host = re.findall('\w{4,5}\:\/\/.*?\/', login_url)[0]
                break
        return {'campus_host':campus_host,'login_url':login_url,'login_host':login_host,'login_type':login_type}       
###############################################################
    @staticmethod        
    def TimeCheck(task,Mod='sign'):
        try:
            if Mod=='sign':
                if task['rateSignDate']:
                    tasktime=f"{task['rateSignDate']} {task['rateTaskBeginTime']}-{task['rateTaskEndTime']}"
                    begin_Day = re.findall(r'([\d]+-[\d]+-[\d]+)',task['rateSignDate'])
                    begin = time.strptime(begin_Day[0]+' '+task['rateTaskBeginTime'],r"%Y-%m-%d %H:%M")
                    end = time.strptime(begin_Day[0]+' '+task['rateTaskEndTime'],r"%Y-%m-%d %H:%M")
                else:
                    tasktime=f"{task['singleTaskBeginTime']}-{task['singleTaskEndTime']}"
                    begin=time.strptime(task['singleTaskBeginTime'],r"%Y-%m-%d %H:%M")
                    end = time.strptime(task['singleTaskEndTime'],r"%Y-%m-%d %H:%M")
                now=time.strptime(task['currentTime'],r"%Y-%m-%d %H:%M")
                taskName=task['taskName']    
            else:
                tasktime=f"{task['startTime']}至{task['endTime']}"
                begin = time.strptime(task['startTime'],r"%Y-%m-%d %H:%M")
                end = time.strptime(task['endTime'],r"%Y-%m-%d %H:%M")
                now=time.strptime(task['currentTime'],r"%Y-%m-%d %H:%M:%S")
                taskName=task['subject']
            begin = time.mktime(begin);now = time.mktime(now);end= time.mktime(end)
            if now >= begin and now <= end:
                Utils.log(f"开始执行任务'{taskName} {tasktime}'")
                return True
            else:
                Utils.log(f"检测到'{taskName} {tasktime}'目前不在任务时间内,请在{begin-now}秒后执行")
        except Exception as e:
            print(f'[{e}]\n{traceback.format_exc()}')
        return None
    
    @staticmethod        
    def address(address):
        print(f"开始获取{address}的具体位置信息")
        url=f"https://restapi.amap.com/v3/geocode/geo?address={address}&output=json&key=  "
        res=requests.get(url=url).json()['geocodes'][0]
        return [res['formatted_address'],res['location'].split(',')[0],res['location'].split(',')[1]]
     
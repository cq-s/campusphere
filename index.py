from Utils import Utils
from Login import Login
from Work import campus_work
import requests,json
GetProxy=False
# @stu.yznu.edu.cn
School={'campus_host': 'https://yznu.campusphere.net/', 'login_url': 'http://authserver.yznu.cn/authserver/login?service=https%3A%2F%2Fyznu.campusphere.net%2Fportal%2Flogin', 'login_host': 'http://authserver.yznu.cn/', 'login_type': 'NOTCLOUD'}
##################################################################
def push(Text,email):
    if email !='':
        url=url='https://prod-168.westus.logic.azure.com:443/workflows/363a7520f4ed4aa49b66d671d557d05c/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IifAnYntQOWrsMgoRbi4f8uqzProrcU9E91xzjg42AM'
        date={"user":email,"title":"今日校园通知","msg":Text}
        r = requests.post(url,json=date).text;print(r)
def work(user):
    statusCode=200
    user['email']=user.get('email','')
    school=School if user['school']=='长江师范学院' else Utils.get_school(user['school'])    
    msg='登录失败'
    login=Login(user,school)
    if login.getCookie():
        msg={}
        Work=campus_work(login)
        msg['签到']=Work.work('签到')
        Work=campus_work(login)
        msg['查寝']=Work.work('查寝')
        Work=campus_work(login)
        msg['信息收集']=Work.collect()
    else:
        statusCode=500
    push(Utils.logs,user['email'])
    return statusCode

    
               
# 阿里云(华为云)的入口函数
def handler(event, context):
    Utils.logs=''
    statusCode=work(event['queryStringParameters'])
    print(event['queryStringParameters'])
    return {
    "isBase64Encoded": False,
    "statusCode": statusCode,
    "headers": {"Content-Type":"text/html; charset=utf-8"},
    "body": Utils.logs}
   

if __name__ == '__main__':
    try:
        with open("userinfo.json", "r") as f:
            userinfo= json.load(f)
            for user in userinfo:
                if user['username'] and user['password']:
                    work(user)
                else:
                    print("请前往userinfo.json文件中配置用户信息")
                Utils.logs=''
        f.close()        
    except:
        print("请确保userinfo.json文件与当前文件在同一路径")
from Utils import Utils
import json
import traceback
doleave = True
debug =False
PhotoUrl='https://wecres.campusphere.net/counselor/sign/1018615910491464/attachment/5f6454d32aeb4a23b1e4bec18bc1798f.png'
API = {
    '签到': {
        'GETTasks': 'wec-counselor-sign-apps/stu/sign/getStuSignInfosInOneDay',
        'GETDetail': 'wec-counselor-sign-apps/stu/sign/detailSignInstance',
        'GenInfo': 'wec-counselor-sign-apps/stu/sign/getStuSignInfosByWeekMonth',
        'PicUploadUrl': 'wec-counselor-sign-apps/stu/obs/getUploadPolicy',
        'GETPicUrl': 'wec-counselor-sign-apps/stu/sign/previewAttachment',
        'Submit': 'wec-counselor-sign-apps/stu/sign/submitSign',
        'checkValidation':'wec-counselor-sign-apps/stu/sign/checkValidation'
    },
    '查寝': {
        'GETTasks': 'wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay',
        'GETDetail': 'wec-counselor-attendance-apps/student/attendance/detailSignInstance',
        'GenInfo': 'wec-counselor-attendance-apps/student/attendance/getStuSignInfosByWeekMonth',
        'PicUploadUrl': 'wec-counselor-sign-apps/stu/obs/getUploadPolicy',
        'GETPicUrl': 'wec-counselor-sign-apps/stu/sign/previewAttachment',
        'Submit': 'wec-counselor-attendance-apps/student/attendance/submitSign',
        'checkValidation':'wec-counselor-attendance-apps/student/attendance/checkValidation'
    },
    '信息收集':{
        'query':'wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList',
        'detailUrl':'wec-counselor-collector-apps/stu/collector/detailCollector',
        'queryHistory':'wec-counselor-collector-apps/stu/collector/queryCollectorHistoryList',
        'getFormUrl':'wec-counselor-collector-apps/stu/collector/getFormFields',
        'PicUploadUrl': 'wec-counselor-collector-apps/stu/obs/getUploadPolicy',
        'GETPicUrl': 'wec-counselor-collector-apps/stu/collector/previewAttachment',
        'Submit':'wec-counselor-collector-apps/stu/collector/submitForm',
        'checkValidation':'wec-counselor-collector-apps/stu/collector/checkValidation'
    }
}

class campus_work:
    # 初始化签到类
    def __init__(self, Login):
        self.session = Login.session
        self.host = Login.campus_host
        self.Trytimes = 0
        self.form = {}
        self.userInfo={'username':Login.username,
                       'school':Login.school,
                       'address':Login.address,
                       'id':Login.id}
        self.headers=  {'User-Agent': 'Mozilla/5.0 (Linux; Android 12; 22021211RC Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MQQBrowser/6.2 TBS/046125 Mobile Safari/537.36 wxwork/4.0.19 MicroMessenger/7.0.1 NetType/WIFI Language/zh Lang/zh ColorScheme/Light',
                'Content-Type':'application/json;charset=UTF-8'}

    def GetTasks(self):
        url = self.host+self.API['GETTasks']
        res = self.session.post(url, headers=self.headers,
                                data=json.dumps({})).json()
        tasklist = []
        Tasks = res['datas']
        if len(Tasks['leaveTasks']) < 1 and len(Tasks['unSignedTasks']) < 1:
            Utils.log(f"检测到当前没有未完成的{self.TaskType}任务")
            return None
        else:
            if len(Tasks['leaveTasks']) > 0:
                if doleave:
                    text = f"请假的{self.TaskType}任务:"
                    for i, task in enumerate(Tasks['leaveTasks']):
                        text = text+str(i+1)+'.'+task['taskName']+' '
                        tasklist.append(task)
                    Utils.log(text)
            if len(Tasks['unSignedTasks']) > 0:
                text = f"未完成的{self.TaskType}任务:"
                for i, task in enumerate(Tasks['unSignedTasks']):
                    text = text+str(i+1)+'.'+task['taskName']+' '
                    tasklist.append(task)
                Utils.log(text)
        for tasks in tasklist:
            if tasks['taskType'] == '6':
                tasklist.remove(tasks)
                Utils.log(
                    f"需要扫码完成的{self.TaskType}任务: '{tasks['taskName']}' 跳过执行")
        if len(tasklist) > 0:
            for tasks in tasklist:
                signtask = None
                if debug:
                    signtask = tasklist[0];break
                if Utils.TimeCheck(tasks):
                    signtask = tasks;break
            if signtask:
                self.taskInfo = {
                    'signInstanceWid': signtask['signInstanceWid'], 'signWid': signtask['signWid']}
                return True
            else:
                print(f"检测到当前没有可以完成的{self.TaskType}任务")
                return None
        else:
            print(f"检测到当前没有可以完成的{self.TaskType}任务")
        return None

    def getDetailTask(self, params):
        url = self.host+self.API['GETDetail']
        res = self.session.post(url, headers=self.headers, data=json.dumps(
            params), verify=False).json()['datas']
        return res

    def GetSignedInfo(self):
        url = self.host+'wec-counselor-sign-apps/stu/sign/getStuIntervalMonths'
        res = self.session.post(url, headers=self.headers,
                                data=json.dumps({}), verify=False).json()
        monthList = [i['id'] for i in res['datas']['rows']]
        monthList.sort(reverse=True)
        for month in monthList:
            data = {"statisticYearMonth": month}
            url = self.host + self.API['GenInfo']
            res = self.session.post(
                url, headers=self.headers, data=json.dumps(data), verify=False).json()
            monthSignList = list(res['datas']['rows'])
            monthSignList.sort(key=lambda x: x['dayInMonth'], reverse=True)
            for daySignList in monthSignList:
                for task in daySignList['signedTasks']:
                    self.SignedTaskId = daySignList['signedTasks'][0]
                    if task['signWid'] == self.taskInfo['signWid']:
                        self.SignedTaskId = task
                        print(f"获取到有相同表单的历史{self.TaskType}任务")
                        return True
        self.task = self.getDetailTask(self.taskInfo)
        if self.task.get('isNeedExtra') != 1:
            return True
        Utils.log('检测到当前任务为新任务,本次请手动进行填写')
        return None

    def fillForm(self):
        SignedTaskId = {
            "signInstanceWid": self.SignedTaskId['signInstanceWid'], "signWid": self.SignedTaskId['signWid']}
        signedTask = self.getDetailTask(SignedTaskId)
        self.task = self.getDetailTask(self.taskInfo)
        self.form['isNeedExtra'] = self.task.get('isNeedExtra', 0)
        if self.form['isNeedExtra'] == 1:
            signedTask['extraFieldItems'] = [{"extraFieldItemValue": i['extraFieldItem'],
                                              "extraFieldItemWid": i['extraFieldItemWid']} for i in signedTask['signedStuInfo']['extraFieldItemVos']]
            self.form['extraFieldItems'] = signedTask['extraFieldItems']
        # 判断签到是否需要照片
        if self.task['isPhoto'] == 1 and signedTask['signPhotoUrl'] == '':
            signedTask['signPhotoUrl'] = PhotoUrl
        self.form['signPhotoUrl'] = signedTask['signPhotoUrl']if self.task['isPhoto'] == 1 else ''
        self.form['position'] = signedTask['signAddress']
        self.form['longitude'] = signedTask['longitude']
        self.form['latitude'] = signedTask['latitude']
        self.userInfo['latitude']=self.form['latitude']; self.userInfo['longitude']=self.form['longitude']
        # 固定部分
        self.form['isMalposition'] = self.task['isMalposition']
        self.form['signInstanceWid'] = self.task['signInstanceWid']
        self.form['abnormalReason'] = ''
        self.form['uaIsCpadaily'] = True
        self.form['signVersion'] = '1.0.0'

    def submitForm(self):
        self.userInfo['latitude']=self.form['latitude'];self.userInfo['longitude']=self.form['longitude']
        self.submitData = self.form
        self.submitApi = self.API['Submit']
        ticket= self.getcaptcha()
        if ticket:
            self.submitData['ticket'] = ticket
        res = Utils.submitFormData(self).json()
        Utils.log(f"{self.TaskType}任务'{self.task['taskName']}'已完成")if res['message'] == 'SUCCESS'else Utils.log(
            f"{self.TaskType}任务'{self.task['taskName']}'执行失败,原因是:{res['message']}")
        return res['message']

    def work(self, TaskType):
        print(f"开始执行{TaskType}任务")
        msg = ''
        while self.Trytimes < 3:
            self.Trytimes += 1
            self.API = API[TaskType]
            self.TaskType = TaskType
            try:
                if self.GetTasks():
                    if self.GetSignedInfo():
                        self.fillForm()
                        msg = self.submitForm()
                else:
                    break
            except Exception as e:
                print(f'[{e}]\n{traceback.format_exc()}')
                msg = '执行出错'
                continue
        return msg
    def GetSignedplace(self):
        if self.userInfo['address']:
            res=self.userInfo['address'];print(f"正在使用传入的地址：{res}用于提交")
            return res
        url = self.host+'wec-counselor-sign-apps/stu/sign/getStuIntervalMonths'
        res = self.session.post(url, headers=self.headers,
                                data=json.dumps({}), verify=False).json()
        monthList = [i['id'] for i in res['datas']['rows']]
        monthList.sort(reverse=True)
        for month in monthList:
            data = {"statisticYearMonth": month}
            url = self.host + 'wec-counselor-sign-apps/stu/sign/getStuSignInfosByWeekMonth'
            res = self.session.post(
                url, headers=self.headers, data=json.dumps(data), verify=False).json()
            monthSignList = list(res['datas']['rows'])
            monthSignList.sort(key=lambda x: x['dayInMonth'], reverse=True)
            for daySignList in monthSignList:
                for task in daySignList['signedTasks']:
                    res = self.session.post(self.host+'wec-counselor-sign-apps/stu/sign/detailSignInstance', headers=self.headers, data=json.dumps(
                {'signInstanceWid': task['signInstanceWid'], 'signWid':task['signWid']}), verify=False).json()['datas']
                    if res.get('signAddress'):
                        print('正在获取历史地址用于提交')
                        return [res['signAddress'],res['longitude'],res['latitude']]
    def getcaptcha(self):
        headers = self.headers
        headers['CpdailyStandAlone']='0';headers['extension']='1'
        url = self.host+self.API['checkValidation']
        deviceId= self.userInfo['id'] if self.userInfo['id'] else Utils.GenDeviceID(self.userInfo['username'])  
        captcha = self.session.post(url=url, headers=headers,data=json.dumps({'deviceId':deviceId}),verify=False).json()['datas']
        if not captcha['validation']:
            return None
        url = self.host + 'captcha-open-api/v1/captcha/create/scenesImage';print("已触发验证码系统，验证中。。。")
        headers['deviceId']=deviceId
        while self.Trytimes < 5:
            self.Trytimes += 1
            question = self.session.post(url=url, headers=headers,params=captcha,verify=False).json()
            hcaptcha=self.session.post(url="https://apple.ruoli.cc/captcha/validate",json=question,timeout=35).json()['data']
            print(hcaptcha)
            data={'scenesImageCode':hcaptcha['code'],'scenesImageCodes':hcaptcha['succCode']}
            captcha.update(data)
            url = self.host + 'captcha-open-api/v1/captcha/validate/scenesImage'
            res = self.session.post(
                url=url, headers=headers,params=captcha,verify=False).json()
            if res['message']=='操作成功':
                print("验证成功");break
            else:
                print("验证失败")
        return res['result']
    def collect(self):
        self.API = API['信息收集']
        msg = ''
        while self.Trytimes < 3:
            self.Trytimes += 1
            try:
                if self.queryForm():
                    if self.GetHistory():
                        self.fill_Form()
                        msg = self.Submit_Form()
                else:
                    break
            except Exception as e:
                print(f'[{e}]\n{traceback.format_exc()}')
                msg = '执行出错'
                continue
        return msg

    def queryForm(self):
        queryUrl = self.host+self.API['query']
        pageSize = 20;pageNumber = 0;totalSize = 1
        params = {"pageSize": pageSize, "pageNumber": 1}
        while pageNumber*pageSize <= totalSize:
            pageNumber += 1
            params["pageNumber"] = pageNumber
            tasks = self.session.post(queryUrl, data=json.dumps(
                params), headers=self.headers, verify=False).json()
            if pageNumber == 1:
                totalSize = tasks['datas']['totalSize']
                if totalSize == 0:
                    Utils.log("没有获取到信息收集任务")
                    return None
            tasklist = tasks['datas']['rows']
            if not debug:
                for task in tasklist:
                    if task['isHandled'] == 1:
                        tasklist.remove(task)
            if len(tasklist) < 1:
                Utils.log('检测到当前没有未完成的信息收集任务')
                return None
            text = "未完成的信息收集任务:"
            for i, task in enumerate(tasklist):
                text = text+str(i+1)+'.'+task['subject']+' '
            Utils.log(text)
            self.collectTask = None
            if debug:
                self.collectTask = tasklist[0]
            for task in tasklist:
                if Utils.TimeCheck(task, 'collect'):
                    self.collectTask = task
                    break
            if  self.collectTask:
                self.instanceWid = self.collectTask.get('instanceWid', '')
                self.taskid = {
                    'collectorWid':  self.collectTask['wid'], 'formWid':  self.collectTask['formWid'],"instanceWid": self.instanceWid}
                detailUrl = self.host+self.API['detailUrl']
                try:
                    self.schoolTaskWid = self.session.post(detailUrl, headers=self.headers, data=json.dumps(
                    self.taskid), verify=False).json()['datas']['collector']['schoolTaskWid']
                except:
                    self.schoolTaskWid=''
                return True
            print("检测到当前没有可以完成的信息收集任务")
            return None

    def GetHistory(self):
        url = self.host+self.API['queryHistory']
        pageSize = 20;pageNumber = 0;totalSize = 1
        params = {"pageNumber": 1, "pageSize": pageSize}
        while pageNumber*pageSize <= totalSize:
            pageNumber += 1
            params["pageNumber"] = pageNumber
            res = self.session.post(
                url, headers=self.headers, data=json.dumps(params), verify=False).json()
            if pageNumber == 1:
                totalSize = res['datas']['totalSize']
                if totalSize < 0:
                    Utils.log('检测到当前任务为新任务请手动进行填写')
                    return None
            for task in res['datas']['rows']:
                if task['isHandled'] == 1 and task['formWid'] == self.taskid['formWid']:
                    self.Historyid = {"formWid": task['formWid'], "instanceWid": task['instanceWid'], "collectorWid": task['wid']}
                    return True
        Utils.log('检测到当前任务为新任务请手动进行填写')
        return None

    def getDetail(self, params):
        getFormUrl = self.host+self.API['getFormUrl']
        params = {"pageSize": 100, "pageNumber": 1,
                  "formWid": params['formWid'], "collectorWid": params['collectorWid'], "instanceWid": params['instanceWid']}
        res = self.session.post(getFormUrl, headers=self.headers, data=json.dumps(
            params), verify=False).json()['datas']['rows']
        return res

    def fill_Form(self):
        form = self.getDetail(self.Historyid)
        for item in form:
            item['show'] = True
            item['formType'] = '0'
            item['sortNum'] = str(item['sort'])
            if item['fieldType'] == '2':
                item['fieldItems'] = list(filter(lambda x: x['isSelected'], item['fieldItems']))
                if item['fieldItems']:
                    item['value'] = item['fieldItems'][0]['itemWid']
            elif item['fieldType'] == '3':
                item['fieldItems'] = list(filter(lambda x: x['isSelected'], item['fieldItems']))
                if item['fieldItems']:
                        item['value'] = ','.join([i['itemWid'] for i in item['fieldItems']])
            elif item['fieldType'] == '4':
                item['value'] =PhotoUrl
        self.form = form

    def Submit_Form(self):
        try:
            address=self.GetSignedplace()
        except:    
            address = Utils.address(self.userInfo['school'])
        self.userInfo['latitude']=address[-1]; self.userInfo['longitude']=address[1]
        self.submitData = {
            "formWid": self.taskid['formWid'],
            "address": address[0],
            "collectWid": self.taskid['collectorWid'],
            "schoolTaskWid": self.schoolTaskWid,
            "uaIsCpadaily": True,
            "latitude": address[-1],
            "longitude": address[1],
            "instanceWid": self.instanceWid,
            "form":self.form
        }
        self.submitApi =self.API['Submit']
        ticket= self.getcaptcha()
        if ticket:
            self.submitData['ticket'] = ticket
        res = Utils.submitFormData(self).json()
        Utils.log(f"信息收集任务'{ self.collectTask['subject']}'已完成") if res['message'] == 'SUCCESS' else Utils.log(
            f"信息收集任务执行失败,原因是:{res['message']}")
        return res['message']
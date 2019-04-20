# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 16:51:25 2019

@author: lei
"""
import os
import re
import sys
import time

import requests
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QGridLayout,
                             QApplication, QTableWidget, QCheckBox, QFileDialog)

sys.path.append(r'E:\DevelopTools\Anaconda3\envs\img\Lib\site-packages')
sys.path.append(r'E:\DevelopTools\Anaconda3\envs\img\Lib\site-packages\PyQt5')


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径


class Web():
    """学校教务网连接模块

    实现教务登陆，爬取信息

    Attributes:
        
        classData:一个list数组，每个元素里保存所有爬取到的课程信息，包括课程名和URL
        path: str,保存文件下载目录
        data：一个dict字典，保存用户登陆信息
        cookies：一个dict字典，保存cookies
        headers：一个dict字典，保存请求头，一定要有'Referer'属性，不然教务会报错
        teacher_url： 课程资源请求URL
        login_url： 登陆请求URL
        Loading_url： 登陆cookies返回URL，登陆分两步，首先是验证，然后再请求得到session
        imgUrl: 验证码请求URL
        session: 保持连接
    """
    classData = []
    path = '大学/'
    data = {
        "username": "",
        "password": "",
        "ranstring": ""}
    cookies = {"username": "",
               'JSESSIONID': '',
               'Upgrade-Insecure-Requests': '1'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        'Referer': 'https://jwc.swjtu.edu.cn/service/login.html'

    }

    teacher_url = r"http://jwc.swjtu.edu.cn/vatuu/StudentTeachResourceAction?setAction=teachCourse"
    login_url = r'http://jwc.swjtu.edu.cn/vatuu/UserLoginAction'
    Loading_url = r'http://jwc.swjtu.edu.cn/vatuu/UserLoadingAction'
    imgUrl = r"http://jwc.swjtu.edu.cn/vatuu/GetRandomNumberToJPEG?test=%d" % time.time()
    session = requests.Session()

    #    首先请求课程首页，获得所有课程信息，然后通过正则提取课程名和URL，将其写入classData中，
    #    并返回一个list
    def getClassList(self):
        r = self.session.get(self.teacher_url, verify=False)  # 请求课程首页
        r.encoding = r.content  # 获取编码规则并设定
        text = r.text  # 得到网页
        # print(text)
        re_string = r'http://+[ ./?%&=\w-]+[^\x00-\xff]+[^\x00-\xff]'  # 匹配URL
        pattern = re.compile(re_string)
        results = pattern.findall(text)  # 匹配所有连接
        for url in results:
            self.classData.append([re.search(r'(?<=courseName=)(.*)', url).group(0), url])
        return self.classData

    #    输入一个list，格式为[‘课程名’，‘url’]，然后请求该url获取该课程的所有资源，下载所有资源
    def getDocuments(self, url):
        s = self.session
        mkdir(self.path + '/' + url[0])  # 创建路径，防止无法下载文件
        r = s.get(url[1], verify=False)  # 请求课件资源页
        r.encoding = r.content  # 获取编码规则并设定
        text = r.text
        # print(text)
        re_string = r'(?<=href="../)([^\s]*)">'  # 匹配URL
        pattern = re.compile(re_string)
        results = pattern.findall(text)  # 匹配所有连接
        #       得到的results的url格式为'vatuu/StudentTeachResourceAction?setAction=
        #       teachResourceView&amp;resourceId=ECA1EB0AE97FFB5D',缺少完整地址，必须补足
        for reslut in results:
            r = s.get(r'http://jwc.swjtu.edu.cn/' + reslut, verify=False)  # 补足连接
            r.encoding = r.content  # 获取编码规则并设定
            text = r.text
            name = re.compile(r'(?<=<td width="40%" style="color: #0EA33F">)(.*)</td>').findall(text)
            download_url = pattern.findall(text)  # 取得单个下载链接
            #            如果资源存在，则下载，如果下载失败或者文件打开失败，则报错，然后继续下载
            try:
                download_url = r'http://jwc.swjtu.edu.cn/' + download_url[0]
                ir = requests.get(download_url, verify=False)

                if ir.status_code == 200:  # 如果网页存在，并正确响应

                    #                    print(self.path+'/'+url[0]+'/'+name[0])
                    f = open(self.path + '/' + url[0] + '/' + name[0], 'wb')
                    f.write(ir.content)
                    f.close()
            #                    print(name[0]+'下载成功\n')
            except:
                #                print(str(name)+'下载错误\n')
                continue

    #    获取验证码，并下载到本地
    def getImage(self):
        r = self.session.get(self.imgUrl, stream=True, headers=self.headers, verify=False)
        self.cookies.update(r.cookies.get_dict())
        extension = os.path.splitext(self.imgUrl)[1]  # 获取扩展名
        imgName = ''.join(["./image", extension])
        with open(imgName, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
            f.close()


web = Web()


class LoginUi(QWidget):
    global web

    def __init__(self):
        super(LoginUi, self).__init__()

        self.initUI()

    def initUI(self):
        self.user_Label = QLabel('用户名')
        self.password_Label = QLabel('密码')
        self.ranstring_Label = QLabel('验证码')
        self.login_button = QPushButton('登陆')
        self.login_button.clicked.connect(self.postInformation)

        self.ranstringImg = QLabel()
        self.getImage()
        self.newRanImg = QPushButton('刷新')
        self.newRanImg.clicked.connect(self.getImage)

        self.userEdit = QLineEdit()
        self.passwordEdit = QLineEdit()
        self.ranstringEdit = QLineEdit()
        self.userEdit.setText(web.data['username'])
        self.passwordEdit.setText(web.data['password'])

        self.ranImg = QPixmap('image')
        self.ranstringImg.setPixmap(self.ranImg)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.user_Label, 1, 0)
        grid.addWidget(self.userEdit, 1, 1, 1, 5)
        grid.addWidget(self.password_Label, 2, 0)
        grid.addWidget(self.passwordEdit, 2, 1, 1, 5)

        grid.addWidget(self.ranstring_Label, 3, 0)
        grid.addWidget(self.ranstringEdit, 3, 1, 1, 3)
        grid.addWidget(self.ranstringImg, 3, 4, 1, 1)
        grid.addWidget(self.newRanImg, 3, 5, 1, 1)

        grid.addWidget(self.login_button, 4, 5)

        self.setLayout(grid)
        self.setGeometry(300, 300, 200, 200)
        self.setWindowTitle('登录器')
        self.show()

    #    获取验证码并显示
    def getImage(self):
        web.getImage()
        self.ranImg = QPixmap('image')
        self.ranstringImg.setPixmap(self.ranImg)

    #    提交登陆信息
    def postInformation(self):
        web.data['username'] = self.userEdit.text()
        web.data['password'] = self.passwordEdit.text()
        web.data['ranstring'] = self.ranstringEdit.text()
        # =============================================================================
        #         print(cookies)
        # =============================================================================
        r = web.session.post(web.login_url, data=web.data, headers=web.headers, verify=False)
        r.encoding = r.content  # 获取编码规则并设定
        text = r.text

        # =============================================================================
        #         print(web.data)
        #         print(text)
        #         print(r.cookies)
        # =============================================================================
        web.session.post(web.Loading_url, data=text.encode('utf-8'), verify=False)
        r.encoding = r.content  # 获取编码规则并设定
        text = r.text

        # =============================================================================
        #         print(text)
        #         print(r.cookies)
        # =============================================================================
        self.hide()
        self.s = DownloadUi()
        self.s.show()


class DownloadUi(QTableWidget):
    global web
    checkBoxList = []
    grid = QGridLayout()
    path = ''

    def __init__(self):
        super(DownloadUi, self).__init__()
        self.initUI()

    def initUI(self):
        self.resize(500, 350)
        self.setWindowTitle('文件下载')
        i = self.getData()
        # self.setShowGrid(False) #是否需要显示网格

        # =============================================================================
        #         self.settableHeader()
        #         self.inputcelldata()
        #         self.settableSelectMode()
        # =============================================================================

        self.downloadBtn = QPushButton('下载', self)
        self.pathBtn = QPushButton('选择文件夹', self)
        self.grid.addWidget(self.downloadBtn, i, 2, 1, 1)
        self.grid.addWidget(self.pathBtn, i, 3, 1, 1)

        self.downloadBtn.clicked.connect(self.download)
        self.pathBtn.clicked.connect(self.selectPath)

    #    获取到课程信息后，动态为每个课程增加选择框，返回课程数量
    def getData(self):
        table = web.getClassList()  # 获取所有可能的课程信息及链接
        i = 0
        self.checkBoxList = locals()  # 动态生成checkBoxList
        self.grid.setSpacing(10)
        for subject in table:
            print(subject[0])
            self.checkBoxList[str(i + 1)] = QCheckBox(subject[0], self)
            self.grid.addWidget(self.checkBoxList[str(i + 1)], i, 0)
            # self.setItem(i,0,QTableWidgetItem(subject[0]))
            i += 1
        self.checkBoxList['0'] = QCheckBox('全选', self)
        self.grid.addWidget(self.checkBoxList['0'], i, 0)
        self.setLayout(self.grid)
        return i

    #    设置文件路径
    def selectPath(self):
        web.path = QFileDialog.getExistingDirectory(self, '选择文件')

    #   下载选择课程的所有资源
    def download(self):
        if self.checkBoxList['0'].isChecked():
            for url in web.classData:
                #                print(url)
                web.getDocuments(url)
                QApplication.processEvents()
        else:
            i = 1
            for url in web.classData:
                if self.checkBoxList[str(i)].isChecked():
                    #                    print(url)
                    web.getDocuments(url)
                    QApplication.processEvents()
                i += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = LoginUi()
    ui.show()
    sys.exit(app.exec_())

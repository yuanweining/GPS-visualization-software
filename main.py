import sys
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QLCDNumber, QTextBrowser, QTextEdit, QTableWidget, QTableWidgetItem
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import *
import math
from PyQt5.Qt import *
from PyQt5.QtCore import QTimer,QDateTime, Qt
import time
from utils import decode_GSV, decode_GGA, decode_RMC 
import serial
import collections
import os

def resource_path(relative_path): #生成exe文件的临时文件
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GUI(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.radar_image = QtGui.QPixmap(resource_path('img/radar3.png'))
        self.gps_image = QtGui.QPixmap(resource_path('img/gps.png'))
        self.glonass_image = QtGui.QPixmap(resource_path('img/glonass.png'))
        self.bds_image = QtGui.QPixmap(resource_path('img/bds.jpg'))
        
        self.middle = [301,306.5]#[351, 356.5]
        self.radius = 220.5
        self.radar = QLabel(self)
        self.satellites_label = []
        self.satellites = []
        self.radar_show()
        
        self.timer1_init()
        
        self.lcd=QLCDNumber(19, self)
        self.lcd.resize(900,150)
        self.lcd.setSegmentStyle(QLCDNumber.Flat)
        self.lcd.move(290,50)
        self.lcd.setLineWidth(0)
        self.lcd.display('2020-01-01 0:0:01')
        
        self.browser_label = QLabel(self)
        self.browser_label.setText("GNSS报文")
        self.browser_label.move(1215,250)
        self.browser_label.setFont(QtGui.QFont('Timers',18))
        self.text_browser = QTextBrowser(self)
        self.text_browser.resize(350,530)
        self.text_browser.move(1100,300)
        self.text_browser.setStyleSheet("border:3px solid black") 
        self.text_browser.setFont(QtGui.QFont('Timers',8))
        self.textEdit=QTextEdit()
        
        self.tableWidget = QtWidgets.QTableWidget(7,1,self)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setVerticalHeaderLabels(['南/北纬','纬度','东/西经', '经度', '航向', '速率', '定位方式'])
        self.tableWidget.setHorizontalHeaderLabels(['数据'])
        self.tableWidget.setGeometry(QtCore.QRect(750, 420, 250, 290))
        self.tableWidget.setShowGrid(False)
        #self.tableWidget.setFont(QtGui.QFont('Timers',10))
        self.Items = []
        for i in range(7):    
            self.Items.append(QTableWidgetItem('--'))
            self.Items[i].setTextAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.tableWidget.setItem(i,0,self.Items[i])
        #self.tableWidget.setVerticalHeaderItem([0,'行1'])
        self.lcd.setLineWidth(0)
        #self.tableWidget.setStyleSheet("border:2px solid black") 
        self.tableWidget.setObjectName("tableWidget")
        
        self.dial1 = QDial(self)
        self.dial1.setFixedSize(100, 100)                     
        self.dial1.setRange(0, 180)                
        self.dial1.setNotchesVisible(True)    
        #self.dial.valueChanged.connect(self.on_change_func)     
        self.dial1.move(750,250)
        self.dial_label1 = QLabel('未定位', self)
        #self.dial_label1.setFont(QFont('Arial Black', 8))
        self.dial_label1.move(750,360)
        self.dial_label1.resize(300,20)
        
        self.dial2 = QDial(self)
        self.dial2.setFixedSize(100, 100)                     
        self.dial2.setRange(0, 180)                
        self.dial2.setNotchesVisible(True)    
        #self.dial.valueChanged.connect(self.on_change_func)     
        self.dial2.move(900,250)
        self.dial_label2 = QLabel('未定位', self)
        #self.dial_label2.setFont(QFont('Arial Black', 8))
        self.dial_label2.move(900,360)
        self.dial_label2.resize(300,20)
        
        
        self.btn1 = QToolButton(self)
        self.btn1.setArrowType(Qt.RightArrow)
        self.btn1.setText("开始")
        self.btn1.resize(100,30)
        self.btn1.move(900,750)
        self.btn1.pressed.connect(self.timer1_start)
        
        self.btn2 = QToolButton(self)
        self.btn2.setText("暂停")
        self.btn2.resize(100,30)
        self.btn2.move(900,800)
        self.btn2.pressed.connect(self.timer1.stop)
        #self.btn.setIcon(QIcon("icon.ico"))
        
        self.combobox_1 = QComboBox(self)
        self.com_list = []
        for i in range(20):
            self.com_list.append('COM'+str(i))
        self.com = 'COM0'
        self.combobox_1.addItems(self.com_list)
        self.combobox_1.setCurrentIndex(0)
        self.combobox_1.currentIndexChanged.connect(self.change_com)
        self.combobox_1.resize(100,30)
        self.combobox_1.move(750,750)
        
        self.combobox_2 = QComboBox(self)
        self.baud_rate_list = ['1200','2400','4800','9600','19200','38400','57600','115200']
        self.baud_rate = 9600
        self.combobox_2.addItems(self.baud_rate_list)
        self.combobox_2.setCurrentIndex(3)
        self.combobox_2.currentIndexChanged.connect(self.change_baud_rate)
        self.combobox_2.resize(100,30)
        self.combobox_2.move(750,800)
        
        self.copy_right = QLabel('copy right 袁伟宁', self)
        self.copy_right.resize(150,30)
        self.copy_right.move(1320,870)
        
        self.setGeometry(200, 100, 1500, 900)
        self.setWindowTitle('GNSS 分析软件')   
        self.show()
        
        self.ser = None
        #self.ser_init()
        self.states = collections.defaultdict(lambda:'') #定位方式，时分秒，年月日，维度，南/北，精度，东/西，航向，速率
        
        
    def ser_init(self):
        if self.ser is not None:
            self.ser = None
        try:
            self.ser = serial.Serial(self.com,self.baud_rate,timeout=5)  
            self.ser.flushInput() 
        except:
            return
        
    def timer1_init(self):
        self.timer1=QTimer(self)
        self.timer1.timeout.connect(self.step)
        self.timer1.start(1000)
        
    def timer1_start(self):
        self.ser_init()
        self.timer1.start(1000)
        
    def change_com(self):
        idx = self.combobox_1.currentIndex()
        self.com = self.com_list[idx]
        
    def change_baud_rate(self):
        idx = self.combobox_2.currentIndex()
        self.baud_rate = int(self.baud_rate_list[idx])
        
    def radar_show(self):
        self.radar.setGeometry(50,250,600,600)
        self.radar.setPixmap(self.radar_image)
        self.radar.setScaledContents(True)
        
    def each_satellite_show(self, i, s_type, item):
        if s_type == 'GPS':
            image = self.gps_image
        elif s_type == 'GLONASS':
            image = self.glonass_image
        elif s_type == 'BDS':
            image = self.bds_image
        else:
            return
        lb = self.satellites_label[i]
        radius = 10
        lb.setGeometry(float(item[0]-radius),float(item[1]-radius),radius*2,radius*2)
        lb.setPixmap(image)
        lb.setScaledContents(True)
        lb.show()
        
    def satellites_show(self):
        for s in self.satellites_label:
            s.hide() 
        self.satellites_label = []
        for i, s in enumerate(self.satellites):
            s_type = s[0]
            elevation = s[1]
            azimuth = s[2]
            SNR = s[3]
            
            cosLen = math.cos(elevation*math.pi/180)*self.radius
            y = -1*math.cos(azimuth*math.pi/180)*cosLen+self.middle[1]
            x = math.sin(azimuth*math.pi/180)*cosLen+self.middle[0]
            self.satellites_label.append(QLabel(self.radar))
            self.each_satellite_show(i, s_type,[x,y])
    
    def time_show(self):
        #self.states = {'local_time_year':'311020','local_time':'090150.00'}
        if self.states['local_time_year'] == '' or self.states['local_time'] == '':
            return
        temp = self.states['local_time_year']
        str1 = '20'+temp[4:6]+'-'+temp[2:4]+'-'+temp[0:2]+' '
        temp = self.states['local_time']
        str2 = str((int(temp[0:2])+8)%24)+':'+temp[2:4]+':'+temp[4:6]
        self.time = str1+str2
        self.lcd.display(self.time)
        
    def browser_show(self):
        for r in self.recv:
            if r[:1] == b"$":
                self.textEdit.setPlainText(r.decode('gbk'))
                self.text_browser.append(self.textEdit.toPlainText())
    
    def frame_show(self):
        self.Items[0] = QTableWidgetItem(self.states['latitude_diretion'])
        self.Items[1] = QTableWidgetItem(self.states['latitude'])
        self.Items[2] = QTableWidgetItem(self.states['longtitude_diretion'])
        self.Items[3] = QTableWidgetItem(self.states['longtitude'])
        self.Items[4] = QTableWidgetItem(self.states['diretion'])
        self.Items[5] = QTableWidgetItem(self.states['speed'])
        self.Items[6] = QTableWidgetItem(self.states['s_type'])
        for i in range(7):    
            self.Items[i].setTextAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.tableWidget.setItem(i,0,self.Items[i])
            
    def dial_show(self):
        self.dial_label1.setText('未定位')
        self.dial_label2.setText('未定位')
        if self.states['latitude'] == '' or self.states['longtitude'] == '':
            return
        if self.states['latitude'] != '':
            self.dial1.setValue(float(self.states['latitude']))
            if self.states['latitude_diretion'] == 'N':
                self.dial_label1.setText('北纬 ' + str(float(self.states['latitude']))[:5] + '°')
            elif self.states['latitude_diretion'] == 'S':
                self.dial_label1.setText('南纬 ' + str(float(self.states['latitude']))[:5] + '°')
        if self.states['longtitude'] != '':
            self.dial2.setValue(float(self.states['longtitude'])) 
            if self.states['longtitude_diretion'] == 'E':
                self.dial_label2.setText('东经 ' + str(float(self.states['longtitude']))[:6] + '°')
            elif self.states['longtitude_diretion'] == 'W':
                self.dial_label2.setText('西经 ' + str(float(self.states['longtitude']))[:6] + '°')
        
            
    def step(self):
        if self.ser is None:
            return
        count = self.ser.inWaiting() 
        if count !=0 :
            self.recv = self.ser.readlines(self.ser.in_waiting)
            print(self.recv)
            self.satellites = []
            self.browser_show()
            for r in self.recv:
                #print(str(r))
                if 'GSV' in str(r):
                    self.satellites += decode_GSV(r) #卫星个数可用len(satellites)
                elif 'GGA' in str(r):
                    decode_GGA(self.states, r)
                elif 'RMC' in str(r):
                    decode_RMC(self.states, r)
            self.satellites_show()
            self.time_show()
            self.frame_show()
            self.dial_show()
        
    
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())
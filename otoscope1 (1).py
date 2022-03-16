from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import sys
import cv2
import numpy as np
from threading import Thread
import time
import queue


from imutils.video import VideoStream
import imutils
from imutils import paths
import os, datetime

from PyQt5.QtCore import Qt

import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) 
form_class = uic.loadUiType("otoscope.ui")[0]
capture=cv2.VideoCapture(0)
# 
# capture1=cv2.VideoCapture(0) 
datestring=datetime.datetime.now().strftime("%Y-%m-%d")
timestring=datetime.datetime.now().strftime("%H-%M-%S")
file=str(datestring)
time_str=str(timestring)
triggerPIN = 33
GPIO.setup(triggerPIN,GPIO.OUT)
m_count=0
v_count=0
mins = 0
sec = 0
period = '00:00'
global frame
out=None
#VIDEO_NAME = 'test.mp4'

def start_record():
    global v_count
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    global out
    out = cv2.VideoWriter('Videos/%s/%s {0:03}.mp4'.format(v_count) %(file,time_str), fourcc, 20.0, (int(capture.get(3)), int(capture.get(4))))
    
    buzzer = GPIO.PWM(triggerPIN, 550) 
    buzzer.start(2)
    time.sleep(0.1)
    w.video_timer.start(50)

def video_frame():
    ret, frame = capture.read() 
    if ret==True:
        global sec, mins
        if sec > 59:
            sec=0
            mins=mins+1
        period = "{:02d}:{:02d}".format(mins,sec)
        cv2.putText(frame,period, (0,100), cv2.FONT_HERSHEY_SIMPLEX, 2.7, (50,50,155),4, cv2.LINE_AA)
        out.write(frame)
        sec+=1

def stop_record():
    w.video_timer.stop()
    out.release()
    global v_count
    v_count+=1
    buzzer = GPIO.PWM(triggerPIN, 550) 
    buzzer.start(2)
    time.sleep(0.1)

def galleryF():
    path = "/home/pi/Pictures/%s"%file
    os.system("pcmanfm \"%s\"" % path)
    
    
class OwnImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()

class MyWindowClass(QtWidgets.QMainWindow, form_class):

    def __init__(self, parent=None):
        global fileName
        super(MyWindowClass, self).__init__()
        uic.loadUi("otoscope.ui", self)
        
        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        self.startButton.pressed.connect(self.start_stream)
        self.imageCapture.pressed.connect(self.saveimage)
        self.startRecord.pressed.connect(start_record)
        self.stopRecord.pressed.connect(stop_record)        
        self.galleryR.pressed.connect(galleryF)
        
        self.exitB.pressed.connect(self.exitFun)
     
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.video_timer = QtCore.QTimer(self)
        self.video_timer.timeout.connect(video_frame)    
        
        thread1= Thread(target = self.push_button).start()
        
    def exitFun(self):
        msg=QMessageBox()
        msg.setWindowTitle("Shutdown")
        msg.setText("Do you really want to shutdown?")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        msg.buttonClicked.connect(self.shutDown)
        x=msg.exec()
        
    def shutDown(self,i):
        if(i.text()== "&Yes"):
            time.sleep(1)
            os.system("sudo shutdown -h now")
        else:
            print('Continue...')
    
    def start_stream(self):
        self.timer.start(50)
        os.makedirs('Pictures/%s'%file,exist_ok=True)
        os.makedirs('Videos/%s'%file,exist_ok=True)
        
    def push_button(self):
        GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        while True:
            if GPIO.input(10) == GPIO.HIGH:
                #time.sleep(0.5)
                self.saveimage()                            
            else:
                continue
        
    def saveimage(self):
        ret, frame = capture.read()
        if self.timer.start:
            cv2.putText(frame, 'Captured!', (0,100), cv2.FONT_HERSHEY_SIMPLEX, 2.7, (50,50,155),4, cv2.LINE_AA)
            self.timer.stop()
        global m_count
        cv2.imwrite('Pictures/%s/%s {0:03}.jpg'.format(m_count) %(file,time_str), frame)
        buzzer = GPIO.PWM(triggerPIN, 550) 
        buzzer.start(2)
        time.sleep(0.1)
        m_count += 1
    
    def video_name(self):
        global VIDEO_NAME 
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        VIDEO_NAME, _ = QFileDialog.getSaveFileName(self,"Save Video","","Video file (*.mp4)", options=options)
        if VIDEO_NAME:
            if not VIDEO_NAME.endswith('.mp4'):
                VIDEO_NAME=VIDEO_NAME+'.mp4'
            self.auto_mode_start()

    def update_frame(self):
        
        ret, frame = capture.read()
        if ret:
            img_height, img_width, img_colors = frame.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])
            if scale == 0:
                scale = 1
        
            frame = cv2.resize(frame, None, fx=scale_w, fy=scale_h, interpolation = cv2.INTER_CUBIC)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame,1)
            height, width, bpc = frame.shape
            bpl = bpc * width
            qimg = QtGui.QImage(frame.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.ImgWidget.setImage(qimg)


    def select_file(self):
        global fileName
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Select File for analysis", "","Video files(*.mp4)", options=options)      
        if fileName:
            self.analysis_timer.start(5)

    def static_frame(self):
        frame = cv2.imread(self.imagePaths[self.index])
        histo=analyze_frame(frame)

        img_height, img_width, img_colors = frame.shape
        scale_w = float(self.window_width) / float(img_width)
        scale_h = float(self.window_height) / float(img_height)
        scale = min([scale_w, scale_h])
        if scale == 0:
            scale = 1          
        frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, bpc = frame.shape
        bpl = bpc * width
        qimg = QtGui.QImage(frame.data, width, height, bpl, QtGui.QImage.Format_RGB888)
        self.histo_source_widget.setImage(qimg)    

        histo = cv2.resize(histo, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
        histo = cv2.cvtColor(histo, cv2.COLOR_BGR2RGB)
        height2, width2, bpc2 = histo.shape
        bp2 = bpc2 * width2
        qimg2 = QtGui.QImage(histo.data, width2, height2, bp2, QtGui.QImage.Format_RGB888)
        self.histo_result_widget.setImage(qimg2)

class SplashScreen(QSplashScreen):
    def __init__(self):
        super(QSplashScreen,self).__init__()
        uic.loadUi('splash.ui',self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        pixmap= QtGui.QPixmap("background.png")
        self.setPixmap(pixmap)
    def progress(self):
        for i in range(100):
            time.sleep(0.1)
            self.progressBar.setValue(i)
            
class MainPage(QDialog):
    def __init__(self):
        super(QDialog,self).__init__()
        uic.loadUi('otoscope.ui',self)


app = QtWidgets.QApplication(sys.argv)

sp=SplashScreen()
sp.show()
sp.progress()
w = MyWindowClass(None)
w.show()
sp.finish(w)
app.exec_()

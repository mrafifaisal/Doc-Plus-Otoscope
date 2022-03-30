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

form_class = uic.loadUiType(".otoscope.ui")[0]
capture=cv2.VideoCapture(0) 
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


def galleryF():
    path = "/home/pi"
    os.system("krusader \"%s\"" % path)
    # krusader pcmanfm
    
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
        
        global fileName,x,y,zoom_flag1, zoom_out_flag1, video_flag
        super(MyWindowClass, self).__init__()
        uic.loadUi(".otoscope.ui", self)
        
        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        self.startButton.pressed.connect(self.start_stream)
        self.imageCapture.pressed.connect(self.saveimage)
        self.startRecord.pressed.connect(self.start_record)
        self.stopRecord.pressed.connect(self.stop_record)        
        self.galleryR.pressed.connect(galleryF)
        self.x=0
        self.y=0
        self.zoom_flag1=False
        self.zoom_out_flag1=False
        self.video_flag=False
        self.exitB.pressed.connect(self.exitFun)
     
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.video_timer = QtCore.QTimer(self)
        self.video_timer.timeout.connect(self.video_frame)    
        
        thread1= Thread(target = self.push_button).start()

    def mousePressEvent(self, QMouseEvent):
        self.x=QMouseEvent.x()
        self.y=QMouseEvent.y()
        if (self.x >= 0 and self.x <= 1000) and (self.y >=0 and self.y <= 470):
            if(not self.zoom_flag1):
                self.zoom_flag1=True
                self.zoom_out_flag1=False
            else: 
                self.zoom_flag1=False
                self.zoom_out_flag1=True


    def zoom_in(self,x,y,frame):
        if (self.x >= 0 and self.x <= 1000) and (self.y >=0 and self.y <= 470):
            max_x=1000
            max_y=470
            min_x=0
            min_y=0
        x1=x - 150
        x2=x + 150
        y1=y - 150
        y2=y + 150
        if x1<min_x:
            x1=min_x
        if x2>max_x:
            x2=1000
        if y1<min_y:
            y1=min_y
        if y2>max_y:
            y2=470        
        frame = frame[y1:y2,x1:x2]
        return frame

        
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
                self.saveimage()                            
            else:
                continue

    def saveimage(self):
        ret, frame = capture.read()
        if self.timer.start:
            self.timer.stop()
        global m_count
        cv2.imwrite('Pictures/%s/%s {0:03}.jpg'.format(m_count) %(file,time_str), frame)
        buzzer = GPIO.PWM(triggerPIN, 550) 
        buzzer.start(2)
        time.sleep(0.1)
        m_count += 1

    def update_frame(self):
        
        ret, frame = capture.read()
        frame = cv2.flip(frame,1)
        if ret:
            frame=cv2.resize(frame,(1000,470))
            if self.zoom_flag1:
                frame=self.zoom_in(self.x,self.y,frame)
                
            if self.video_flag:
                global sec, mins
                if sec > 59:
                    sec=0
                    mins=mins+1
                period = "{:02d}:{:02d}".format(mins,sec)
                cv2.putText(frame,period, (500,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (50,50,155),4, cv2.LINE_AA)
                sec+=1
                out.write(frame)
                
            img_height, img_width, img_colors = frame.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])
            
            if scale == 0:
                scale = 1
        
            frame = cv2.resize(frame, None, fx=scale_w, fy=scale_h, interpolation = cv2.INTER_CUBIC)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            height, width, bpc = frame.shape
            bpl = bpc * width
            qimg = QtGui.QImage(frame.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.ImgWidget.setImage(qimg)
            
    def start_record(self):
        global v_count
        self.video_flag=True
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        global out
        out = cv2.VideoWriter('Videos/%s/%s {0:03}.mp4'.format(v_count) %(file,time_str), fourcc, 10.0, (int(capture.get(3)), int(capture.get(4))))
        buzzer = GPIO.PWM(triggerPIN, 550) 
        buzzer.start(2)
        time.sleep(0.1)
        w.video_timer.start(50)

    def video_frame(self):
        ret, frame = capture.read() 
        if ret==True:
            out.write(frame)

    def stop_record(self):
        w.video_timer.stop()
        out.release()
        global v_count
        v_count+=1
        buzzer = GPIO.PWM(triggerPIN, 550) 
        buzzer.start(2)
        time.sleep(0.1)
        self.video_flag=False


class SplashScreen(QSplashScreen):
    def __init__(self):
        super(QSplashScreen,self).__init__()
        uic.loadUi('.splash.ui',self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        pixmap= QtGui.QPixmap(".background.png")
        self.setPixmap(pixmap)
    def progress(self):
        for i in range(100):
            time.sleep(0.01)
            self.progressBar.setValue(i)
            
class MainPage(QDialog):
    def __init__(self):
        super(QDialog,self).__init__()
        uic.loadUi('.otoscope.ui',self)


app = QtWidgets.QApplication(sys.argv)

sp=SplashScreen()
sp.show()
sp.progress()
w = MyWindowClass(None)
w.show()
sp.finish(w)
app.exec_()

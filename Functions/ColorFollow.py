#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import math
import threading
import numpy as np
import pandas as pd
from hiwonder.PID import PID
import hiwonder.Misc as Misc
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from CameraCalibration.CalibrationConfig import *

#跟随 

debug = False

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

#加载参数
param_data = np.load(calibration_param_path + '.npz')

#获取参数
mtx = param_data['mtx_array']
dist = param_data['dist_array']
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (640, 480), 0, (640, 480))
mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (640, 480), 5)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

lab_data = None
servo_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

__target_color = ('green',)
# 设置检测颜色
def setBallTargetColor(target_color):
    global __target_color

    __target_color = target_color
    return (True, ())

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo_data['servo1'], 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)

load_config()

d_x = 20
d_y = 20
step = 1
x_dis = servo_data['servo2']
y_dis = servo_data['servo1']
start_count = True
centerX, centerY = -2, -2
x_pid = PID(P=0.4, I=0.02, D=0.02)#pid初始化
y_pid = PID(P=0.4, I=0.02, D=0.02)
# 变量重置
def reset():
    global d_x, d_y
    global start_count
    global step, step_
    global x_dis, y_dis
    global __target_color
    global centerX, centerY

    d_x = 20
    d_y = 20
    step = 1
    x_pid.clear()
    y_pid.clear()
    x_dis = servo_data['servo2']
    y_dis = servo_data['servo1']
    start_count = True
    __target_color = ()
    centerX, centerY = -2, -2
    
# app初始化调用
def init():
    print("Follow Init")
    load_config()
    initMove()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("Follow Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    print("Follow Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    AGC.runActionGroup('stand_slow')
    print("Follow Exit")

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp >= 100:  # 只有在面积大于设定值时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  # 返回最大的轮廓

CENTER_X = 320
circle_radius = 0
#执行动作组
def move():
    
    while True:
        if __isRunning:
            if centerX >= 0:
                if centerX - CENTER_X > 100 or x_dis - servo_data['servo2'] < -100:  # 不在中心，根据方向让机器人转向一步
                    AGC.runActionGroup('right_move_fast')
                elif centerX - CENTER_X < -100 or x_dis - servo_data['servo2'] > 100:
                    AGC.runActionGroup('left_move_fast')                        
                elif 100 > circle_radius > 0:
                    AGC.runActionGroup('go_forward_fast')
                elif 180 < circle_radius:
                    AGC.runActionGroup('back_fast')
            else:
                time.sleep(0.01)
        else:
            time.sleep(0.01)

#启动动作的线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

radius_data = []
size = (320, 240)
def run(img):
    global radius_data
    global x_dis, y_dis
    global centerX, centerY, circle_radius
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning or __target_color == ():
        return img
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)   
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    
    area_max = 0
    areaMaxContour = 0
    
    frame_mask_combined = None  # 创建合并的掩码
    
    for i in lab_data:
        if i in __target_color:
            detect_color = i
            frame_mask = cv2.inRange(frame_lab,
                                     (lab_data[i]['min'][0],
                                      lab_data[i]['min'][1],
                                      lab_data[i]['min'][2]),
                                     (lab_data[i]['max'][0],
                                      lab_data[i]['max'][1],
                                      lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
            eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))  #腐蚀
            dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))) #膨胀

            # 合并所有目标颜色的掩码
            if frame_mask_combined is None:
                frame_mask_combined = dilated
            else:
                frame_mask_combined = cv2.bitwise_or(frame_mask_combined, dilated)
    if frame_mask_combined is not None:
        contours = cv2.findContours(frame_mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # 找出轮廓
        areaMaxContour, area_max = getAreaMaxContour(contours)  # 找出最大轮廓
        
    if areaMaxContour is not None and area_max > 100:  # 有找到最大面积
        rect = cv2.minAreaRect(areaMaxContour)#最小外接矩形
        box = np.int0(cv2.boxPoints(rect))#最小外接矩形的四个顶点
        for j in range(4):
            box[j, 0] = int(Misc.map(box[j, 0], 0, size[0], 0, img_w))
            box[j, 1] = int(Misc.map(box[j, 1], 0, size[1], 0, img_h))

        cv2.drawContours(img, [box], -1, (0,255,255), 2)#画出四个点组成的矩形
        #获取矩形的对角点
        ptime_start_x, ptime_start_y = box[0, 0], box[0, 1]
        pt3_x, pt3_y = box[2, 0], box[2, 1]
        radius = abs(ptime_start_x - pt3_x)
        centerX, centerY = int((ptime_start_x + pt3_x) / 2), int((ptime_start_y + pt3_y) / 2)#中心点       
        cv2.circle(img, (centerX, centerY), 5, (0, 255, 255), -1)#画出中心点
          
        use_time = 0       
        
        radius_data.append(radius)
        data = pd.DataFrame(radius_data)
        data_ = data.copy()
        u = data_.mean()  # 计算均值
        std = data_.std()  # 计算标准差

        data_c = data[np.abs(data - u) <= std]
        circle_radius = round(data_c.mean()[0], 1)
        if len(radius_data) == 5:
            radius_data.remove(radius_data[0])
            
        #print(circle_radius)
        x_pid.SetPoint = img_w/2 #设定           
        x_pid.update(centerX) #当前
        dx = int(x_pid.output)
        use_time = abs(dx*0.00025)
        x_dis += dx #输出           
        
        x_dis = servo_data['servo2'] - 400 if x_dis < servo_data['servo2'] - 400 else x_dis          
        x_dis = servo_data['servo2'] + 400 if x_dis > servo_data['servo2'] + 400 else x_dis
            
        y_pid.SetPoint = img_h/2
        y_pid.update(centerY)
        dy = int(y_pid.output)
        use_time = round(max(use_time, abs(dy*0.00025)), 5)
        y_dis += dy
        
        y_dis = servo_data['servo1'] if y_dis < servo_data['servo1'] else y_dis
        y_dis = 2000 if y_dis > 2000 else y_dis    
        
        Board.setPWMServoPulse(1, y_dis, use_time*1000)
        Board.setPWMServoPulse(2, x_dis, use_time*1000)
        time.sleep(use_time)
    else:
        centerX, centerY = -1, -1
   
    #img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)  # 畸变矫正 

    return img

if __name__ == '__main__':
    init()
    start()
    __target_color = ('red','green','blue')
    open_once = yaml_handle.get_yaml_data('/boot/camera_setting.yaml')['open_once']
    if open_once:
        my_camera = cv2.VideoCapture('http://127.0.0.1:8080/?action=stream?dummy=param.mjpg')
    else:
        my_camera = Camera.Camera()
        my_camera.camera_open() 
    AGC.runActionGroup('stand')
    while True:
        ret, img = my_camera.read()
        if img is not None:
            frame = img.copy()
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()

#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TonyPi/')

import os
import time
import cv2
import numpy as np
import threading
import traceback
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.Camera as Camera
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from CameraCalibration.CalibrationConfig import *

class ObjectDetection:
    def __init__(self):
        # 加载舵机参数
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)
        
        # 初始化ASR和TTS模块
        self.asr_tts_ok = True
        try:
            self.asr = ASR.ASR()
            self.tts = TTS.TTS()
            
            self.asr.eraseWords()
            self.asr.setMode(1)  # 1、循环模式 2、口令模式
            
            # 口令
            self.asr.addWords(1, 'kai shi')  # 激活词：开始
            self.asr.addWords(2, 'zhe shi shen me')  # 这是什么
            
            # 舵机初始化
            data = self.asr.getResult()
            Board.setPWMServoPulse(1, 1500, 500)
            Board.setPWMServoPulse(2, self.servo_data['servo2'], 500)
            AGC.runActionGroup('stand')
            
            # 直接使用TTS发声，检测是否可用
            self.tts.TTSModuleSpeak('[h0][v10][m3]', '准备就绪')
            print("ASR和TTS模块初始化成功")
        except Exception as e:
            print(f"ASR或TTS初始化失败: {e}")
            print(f"详细错误: {traceback.format_exc()}")
            self.asr_tts_ok = False
        
        # 初始化相机
        self.camera = Camera.Camera()
        self.camera.camera_open()
        
        # 加载相机校准参数
        param_data = np.load(calibration_param_path + '.npz')
        self.mtx = param_data['mtx_array']
        self.dist = param_data['dist_array']
        self.newcameramtx, self.roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (640, 480), 0, (640, 480))
        self.mapx, self.mapy = cv2.initUndistortRectifyMap(self.mtx, self.dist, None, self.newcameramtx, (640, 480), 5)
        
        # 使用MobileNet SSD模型
        self.classes, self.english_classes, self.net = self.load_model()
        
        # 创建窗口显示结果
        cv2.namedWindow('Detection Result', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detection Result', 640, 480)
        
        # 保存最后的检测结果
        self.last_result = None
        self.last_frame = None
        
        print('''当前为循环模式，每次说指令前不需要说出激活词。
【语音指令说明】：
1 : 开始              -> 激活语音识别
2 : 这是什么          -> 识别物体
''')
        
        print("物体识别初始化完成")
        time.sleep(2)
        
    def load_model(self):
        # 使用MobileNet SSD模型
        print("正在加载模型...")
        model_path = '/home/pi/TonyPi/models/'
        os.makedirs(model_path, exist_ok=True)
        
        # 定义MobileNet SSD能识别的类别（中英文对照）
        english_classes = {
            0: "background",
            1: "airplane", 2: "bicycle", 3: "bird", 4: "boat", 
            5: "bottle", 6: "bus", 7: "car", 8: "cat", 9: "chair", 
            10: "cow", 11: "dining table", 12: "dog", 13: "horse", 
            14: "motorcycle", 15: "person", 16: "potted plant", 
            17: "sheep", 18: "sofa", 19: "train", 20: "tv monitor"
        }
        
        chinese_classes = {
            0: "背景",
            1: "飞机", 2: "自行车", 3: "鸟", 4: "船", 
            5: "瓶子", 6: "公共汽车", 7: "汽车", 8: "猫", 9: "椅子", 
            10: "奶牛", 11: "餐桌", 12: "狗", 13: "马", 
            14: "摩托车", 15: "人", 16: "盆栽植物", 
            17: "羊", 18: "沙发", 19: "火车", 20: "电视显示器"
        }
        
        prototxt = os.path.join(model_path, 'MobileNetSSD_deploy.prototxt')
        model = os.path.join(model_path, 'MobileNetSSD_deploy.caffemodel')
        
        # 检查模型文件是否存在
        if not os.path.exists(prototxt) or not os.path.exists(model):
            print(f"模型文件不存在，请下载MobileNet SSD模型到 {model_path}")
            print("下载地址: https://github.com/chuanqi305/MobileNet-SSD")
            # 尝试使用内置模型
            try:
                # 使用OpenCV内置的人脸检测器作为备用
                net = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                print("已加载备用人脸检测器")
                return {"face": "人脸"}, {"face": "Face"}, net
            except Exception as e:
                print(f"加载备用检测器失败: {e}")
                print(f"详细错误: {traceback.format_exc()}")
                return chinese_classes, english_classes, None
        else:
            try:
                net = cv2.dnn.readNetFromCaffe(prototxt, model)
                net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                print("已加载MobileNet SSD模型")
                return chinese_classes, english_classes, net
            except Exception as e:
                print(f"加载模型失败: {e}")
                print(f"详细错误: {traceback.format_exc()}")
                return chinese_classes, english_classes, None
    
    def detect_objects(self, frame):
        if self.net is None:
            return []
            
        # 检查是级联分类器还是深度学习模型
        if isinstance(self.net, cv2.CascadeClassifier):
            # 使用级联分类器检测人脸
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.net.detectMultiScale(gray, 1.3, 5)
            
            results = []
            for (x, y, w, h) in faces:
                results.append({
                    'class': "人脸",
                    'class_en': "Face",
                    'confidence': 0.9,  # 固定置信度
                    'box': [x, y, w, h]
                })
            return results
        else:
            # 使用MobileNet SSD
            try:
                # 预处理图像 - 使用更小的尺寸加快速度
                (h, w) = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                
                # 前向传播
                self.net.setInput(blob)
                detections = self.net.forward()
                
                # 处理检测结果
                results = []
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    # 过滤掉低置信度的检测结果，降低阈值以检测更多物体
                    if confidence > 0.3:
                        idx = int(detections[0, 0, i, 1])
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")
                        
                        # 确保边界框在图像范围内
                        startX = max(0, startX)
                        startY = max(0, startY)
                        endX = min(w, endX)
                        endY = min(h, endY)
                        
                        # 添加到结果列表，同时保存中文和英文类别
                        results.append({
                            'class': self.classes.get(idx, "未知物体"),
                            'class_en': self.english_classes.get(idx, "Unknown"),
                            'confidence': float(confidence),
                            'box': [startX, startY, endX - startX, endY - startY]
                        })
                return results
            except Exception as e:
                print(f"检测过程出错: {e}")
                print(f"详细错误: {traceback.format_exc()}")
                return []
    
    def draw_detections(self, frame, detections):
        for obj in detections:
            box = obj['box']
            x, y, w, h = box
            
            # 绘制边界框
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 绘制标签 - 使用英文类别名称
            label = f"{obj['class_en']}: {obj['confidence']:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame
    
    def speak_results(self, detections):
        if not self.asr_tts_ok:
            # 如果TTS不可用，只在控制台打印结果
            return self.print_results(detections)
            
        if not detections:
            try:
                self.tts.TTSModuleSpeak('', '我没有识别出任何物体')
                time.sleep(2)  # 给TTS一些播放时间
            except Exception as e:
                print("语音播报失败，改为打印结果")
                print("我没有识别出任何物体")
                self.asr_tts_ok = False
            return
        
        # 按置信度排序，取前三个最可能的物体
        top_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:3]
        
        try:
            if len(top_detections) == 1:
                obj = top_detections[0]
                message = f'这是{obj["class"]}'
                self.tts.TTSModuleSpeak('', message)
                print(message)
            else:
                objects_text = '、'.join([obj['class'] for obj in top_detections])
                message = f'我看到了{objects_text}'
                self.tts.TTSModuleSpeak('', message)
                print(message)
            time.sleep(2)  # 给TTS一些播放时间
        except Exception as e:
            print(f"语音播报失败: {e}，改为打印结果")
            self.print_results(top_detections)
            self.asr_tts_ok = False
    
    def print_results(self, detections):
        if not detections:
            print("未检测到任何物体")
            return
            
        # 按置信度排序，取前三个最可能的物体
        top_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:3]
        
        if len(top_detections) == 1:
            obj = top_detections[0]
            print(f"这是{obj['class']}（{obj['class_en']}），置信度: {obj['confidence']:.2f}")
        else:
            print("检测结果:")
            for i, obj in enumerate(top_detections):
                print(f"{i+1}. {obj['class']}（{obj['class_en']}），置信度: {obj['confidence']:.2f}")
            
            objects_text = '、'.join([obj['class'] for obj in top_detections])
            print(f"总结: 我看到了{objects_text}")
    
    def display_thread(self):
        """持续显示最新的检测结果"""
        while not self.exit_flag:
            if self.last_frame is not None:
                cv2.imshow('Detection Result', self.last_frame)
                key = cv2.waitKey(1)
                if key == 27:  # ESC键退出
                    self.exit_flag = True
            time.sleep(0.03)  # 降低刷新频率减轻CPU负担
    
    def manual_detection(self):
        """手动触发检测（不依赖语音）"""
        # 捕获一帧图像
        ret, frame = self.camera.read()
        if not ret:
            print("无法获取图像")
            return
        
        # 图像校正
        frame = cv2.remap(frame, self.mapx, self.mapy, cv2.INTER_LINEAR)
        
        # 检测物体
        detections = self.detect_objects(frame)
        
        # 在图像上标记检测结果
        result_frame = self.draw_detections(frame.copy(), detections)
        
        # 保存最新结果
        self.last_frame = result_frame
        self.last_result = detections
        
        # 保存结果图像
        cv2.imwrite('/home/pi/TonyPi/detection_result.jpg', result_frame)
        
        # 输出检测结果
        self.speak_results(detections)
    
    def run(self):
        self.exit_flag = False
        
        # 启动显示线程
        display_thread = threading.Thread(target=self.display_thread)
        display_thread.daemon = True
        display_thread.start()
        
        try:
            print("开始运行物体检测程序")
            print("语音控制模式: 请说""开始""激活，然后说""这是什么""进行识别")
            print("或按下Enter键手动触发检测")
            print("提示：循环模式下无需说出激活词")

            while not self.exit_flag:
                try:
                    # 获取语音命令
                    data = self.asr.getResult()
                    if data:
                        print(f'识别编号: {data}')
                        if data == 2:  # "这是什么"
                            print("收到语音命令：这是什么")
                            self.tts.TTSModuleSpeak('', '好的')
                            time.sleep(0.5)  # 给TTS一些播放时间
                            self.manual_detection()
                except Exception as e:
                    print(f"获取语音命令失败: {e}")
                    print(f"详细错误: {traceback.format_exc()}")
                
                # 检查键盘输入(保留功能)
                import select
                import sys
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.readline().strip()
                    if key == '':  # Enter键
                        print("手动触发检测...")
                        self.manual_detection()
                    elif key.lower() == 'q':
                        break
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("程序被用户中断")
        finally:
            self.exit_flag = True
            display_thread.join(timeout=1.0)
            cv2.destroyAllWindows()
            self.camera.camera_close()
            print("物体检测程序已结束")

if __name__ == '__main__':
    detector = ObjectDetection()
    detector.run() 
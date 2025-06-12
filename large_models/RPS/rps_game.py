#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TonyPi/')

import os
import time
import cv2
import random
import hiwonder.Camera as Camera
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from ActionGroupDict import *
from dashscope import MultiModalConversation
import traceback

# 配置API密钥和模型名称
API_KEY = ''
MODEL = 'qwen-vl-max-latest'

# 定义猜拳选项
RPS_OPTIONS = ["石头", "剪刀", "布"]

class RPSGame:
    def __init__(self):
        # 加载舵机参数
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)
        
        # 初始化相机
        self.camera = Camera.Camera()
        self.camera.camera_open()
        
        # 初始化ASR和TTS
        try:
            self.asr = ASR.ASR()
            self.tts = TTS.TTS()
            
            # 清除已有词条
            self.asr.eraseWords()
            self.asr.setMode(1)  # 循环模式
            
            # 添加激活词
            self.asr.addWords(1, 'cai quan')  # 激活词：猜拳
            self.asr.addWords(1, 'zai lai')  # 激活词：再来
            
            # 舵机初始化
            data = self.asr.getResult()
            Board.setPWMServoPulse(1, 1500, 500)
            Board.setPWMServoPulse(2, self.servo_data['servo2'], 500)
            AGC.runActionGroup('stand')
            
            # 初始化完成提示
            print("测试TTS...")
            self.tts.TTSModuleSpeak('[h0][v10]', '猜拳游戏准备就绪')
            time.sleep(1)
            print("TTS测试完成")
            
            print("ASR和TTS模块初始化成功")
            self.asr_tts_ok = True
        except Exception as e:
            print("ASR或TTS初始化失败:", e)
            print(traceback.format_exc())
            self.asr_tts_ok = False
        
        print('''当前为循环模式，可以直接说"猜拳"开始游戏
【语音指令说明】：
1 : 猜拳 (cai quan)  -> 开始猜拳游戏
2 : 再来 (zai lai)  -> 重新开始猜拳游戏
''')
        time.sleep(2)

    def capture_image(self, save_path='/home/pi/RPS/rps_last.jpg'):
        """捕获图像"""
        ret, frame = self.camera.read()
        if not ret:
            print("拍照失败")
            return None
        cv2.imwrite(save_path, frame)
        print(f"图像已保存至 {save_path}")
        return save_path

    def recognize_gesture(self, image_path):
        """调用大模型API识别手势"""
        if not os.path.exists(image_path):
            print(f"图像文件不存在: {image_path}")
            return "无结果"
            
        image_uri = f'file://{image_path}'
        messages = [
            {"role": "system", "content": [{"text": "你是一个猜拳游戏的裁判。你需要识别图片中的手势是石头、剪刀还是布。只返回'石头'、'剪刀'、'布'或'无结果'之一，不要返回其他内容。"}]},
            {"role": "user", "content": [{"image": image_uri}, {"text": "这个手势是什么？只回答'石头'、'剪刀'、'布'或'无结果'之一，不要回答其它任何内容。"}]}
        ]
        try:
            print("正在调用大模型API识别手势...")
            resp = MultiModalConversation.call(
                api_key=API_KEY,
                model=MODEL,
                messages=messages
            )
            
            if (resp and "output" in resp and 
                "choices" in resp["output"] and 
                len(resp["output"]["choices"]) > 0 and
                "message" in resp["output"]["choices"][0]):
                
                message = resp["output"]["choices"][0]["message"]
                if hasattr(message, "content") and len(message.content) > 0:
                    if "text" in message.content[0]:
                        txt = message.content[0]["text"].strip()
                        
                        # 确保结果是四个选项之一
                        if "石头" in txt:
                            return "石头"
                        elif "剪刀" in txt:
                            return "剪刀"
                        elif "布" in txt:
                            return "布"
                        else:
                            return "无结果"
            
            print("API返回格式异常或无法识别")
            return "无结果"
                
        except Exception as e:
            print("识别API调用失败:", e)
            traceback.print_exc()
            return "无结果"

    def robot_choice(self):
        """机器人随机选择出拳"""
        return random.choice(RPS_OPTIONS)

    def judge_winner(self, robot, human):
        """判断胜负"""
        if human == "无结果":
            return "无效"
        
        if robot == human:
            return "平局"
        
        if (robot == "石头" and human == "剪刀") or \
           (robot == "剪刀" and human == "布") or \
           (robot == "布" and human == "石头"):
            return "机器人胜"
        else:
            return "人类胜"

    def speak(self, text):
        """TTS播报"""
        try:
            self.tts.TTSModuleSpeak('[h0][v10]', text)
            # 给TTS足够的播放时间
            sleep_time = min(max(len(text) * 0.15, 0.8), 3)
            time.sleep(sleep_time)
        except Exception as e:
            print(f"TTS播放失败: {e}")
            print(traceback.format_exc())
            print(f"语音播报失败，文本内容: {text}")

    def play_game(self):
        """执行一次猜拳游戏"""
        # 播放开始提示
        self.speak("剪刀石头布")
        time.sleep(0.5)
        
        # 机器人选择
        robot_gesture = self.robot_choice()
        print(f"机器人出: {robot_gesture}")

        if robot_gesture == "剪刀":
            AGC.runActionGroup('jiandao')
        elif robot_gesture == "石头":
            AGC.runActionGroup('shitou')
        elif robot_gesture == "布":
            AGC.runActionGroup('bu')
        
        # 捕获图像
        path = self.capture_image()
        if not path:
            self.speak("拍照失败")
            return
        
        # 识别人类手势
        human_gesture = self.recognize_gesture(path)
        print(f"识别结果: {human_gesture}")
        
        # 宣布结果
        # self.speak(f"我出{robot_gesture}，你出{human_gesture}")
        # time.sleep(0.5)
        
        # 判断胜负
        result = self.judge_winner(robot_gesture, human_gesture)
        print(f"结果: {result}")
        
        # 根据结果执行相应动作和语音
        if result == "机器人胜":
            self.speak("哈哈，我赢了")
            AGC.runActionGroup('chest')  # 执行庆祝动作
        elif result == "人类胜":
            self.speak("呜呜呜，我输了")
            AGC.runActionGroup('cry')  # 执行哭动作
        elif result == "平局":
            self.speak("居然平了，再来")
        else:
            self.speak("没看清楚，再来")

    def run(self):
        print("猜拳游戏已启动，等待语音指令...")
        try:
            while True:
                try:
                    # 获取语音命令
                    data = self.asr.getResult()
                    if data == 1:  # 检测到指令
                        print(f'识别编号: {data}')
                        print("收到语音命令，开始猜拳游戏")
                        self.play_game()
                except Exception as e:
                    print(f"处理语音命令失败: {e}")
                    print(traceback.format_exc())
                
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("程序中止")
        finally:
            self.cleanup()

    def cleanup(self):
        self.camera.camera_close()
        print("摄像头已关闭")

if __name__ == '__main__':
    rps_game = RPSGame()
    rps_game.run() 
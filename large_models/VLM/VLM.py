#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TonyPi/')

import os
import time
import cv2
import hiwonder.Camera as Camera
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from ActionGroupDict import *
from dashscope import MultiModalConversation
import traceback
import re

API_KEY = ''
TRIGGER_WORD = "这是什么"
MODEL = 'qwen-vl-max-latest'
TRIGGER_WORDS = [2, 3, 4, 5]

class VoiceActivatedVision:
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
            self.asr.addWords(1, 'kai shi')  # 激活词：开始
            
            # 添加触发词
            self.asr.addWords(2, 'zhe shi shen me')  # 这是什么
            
            # 舵机初始化
            data = self.asr.getResult()
            Board.setPWMServoPulse(1, 1500, 500)
            Board.setPWMServoPulse(2, self.servo_data['servo2'], 500)
            AGC.runActionGroup('stand')
            
            # 初始化完成提示 - 简短的文本测试TTS
            print("测试TTS...")
            # 调用TTS
            self.tts.TTSModuleSpeak('[h0][v10]', '我准备好了')
            time.sleep(1)  # 给TTS足够的播放时间
            print("TTS测试完成")
            
            print("ASR和TTS模块初始化成功")
            self.asr_tts_ok = True
        except Exception as e:
            print("ASR或TTS初始化失败:", e)
            print(traceback.format_exc())
            self.asr_tts_ok = False
        
        print('''当前为循环模式，可以直接说"这是什么"进行识别
【语音指令说明】：
2 : 这是什么        -> 识别图像内容
''')
        time.sleep(2)

    def capture_image(self, save_path='/home/pi/vision_last.jpg'):
        ret, frame = self.camera.read()
        if not ret:
            print("拍照失败")
            return None
        cv2.imwrite(save_path, frame)
        print(f"图像已保存至 {save_path}")
        return save_path

    def describe_image(self, image_path):
        """调用大模型API描述图像，确保返回字符串类型"""
        if not os.path.exists(image_path):
            print(f"图像文件不存在: {image_path}")
            return "图像文件不存在"
            
        image_uri = f'file://{image_path}'
        messages = [
            {"role": "system", "content": [{"text": "You are a helpful assistant."}]},
            {"role": "user", "content": [{"image": image_uri}, {"text": "图片里内容是什么？请直接给我结果，使用标点符号分隔句子，每一个分隔的句子一定不能超过8个字，回答语言自然一点，总长度不超过100字"}]}
        ]
        try:
            print("正在调用大模型API...")
            resp = MultiModalConversation.call(
                api_key=API_KEY,
                model=MODEL,
                messages=messages
            )
            
            # 确保我们能从响应中提取文本
            if (resp and "output" in resp and 
                "choices" in resp["output"] and 
                len(resp["output"]["choices"]) > 0 and
                "message" in resp["output"]["choices"][0]):
                
                message = resp["output"]["choices"][0]["message"]
                if hasattr(message, "content") and len(message.content) > 0:
                    if "text" in message.content[0]:
                        txt = message.content[0]["text"]
                        # 确保返回的是字符串，并进行清理
                        result = str(txt).strip()
                        # 移除可能导致TTS问题的特殊字符，但保留标点符号
                        result = self.clean_text_for_tts(result, keep_punctuation=True)
                        return result
                    else:
                        print("API返回内容中没有text字段")
                else:
                    print("API返回内容格式异常，没有content字段或content为空")
                
                # 如果无法提取文本，返回整个响应的字符串表示
                return "API返回格式异常"
            else:
                print("API返回格式异常:", resp)
                return "API返回格式异常"
                
        except Exception as e:
            print("识图API调用失败:", e)
            traceback.print_exc()
            return f"识别失败: {str(e)}"
    
    def clean_text_for_tts(self, text, keep_punctuation=False):
        """清理文本，移除可能导致TTS问题的特殊字符"""
        if not isinstance(text, str):
            return str(text)
            
        # 移除markdown标记
        text = text.replace('```', '').replace('`', '')
        
        # 保留或移除标点符号
        if not keep_punctuation:
            punctuation = ['，', '。', '！', '？', '；', '：', '"', '"', ''', ''', '、', '《', '》', '（', '）', '【', '】', '.', ',', '!', '?', ';', ':', '"', "'", '(', ')', '[', ']', '{', '}']
            for p in punctuation:
                text = text.replace(p, '')
        
        # 移除可能导致TTS问题的其他特殊字符
        problematic_chars = ['*', '#', '_', '=', '+', '|', '~', '>', '<']
        for char in problematic_chars:
            text = text.replace(char, '')
            
        return text

    def safe_speak(self, text):
        """安全的TTS播报函数，处理所有可能的异常"""
        if not isinstance(text, str):
            print(f"警告: 传入的不是字符串类型，而是 {type(text)}")
            # 转换为字符串
            text = str(text)
        
        # 如果是简短命令，直接播放
        if len(text) <= 10:
            self._speak_segment(text)
            return
            
        print(f"准备TTS播放文本 (长度:{len(text)}): '{text}'")
        
        # 按标点符号分段
        segments = self.split_by_punctuation(text)
        
        # 如果没有分段成功或只有一段，则按长度分段
        if not segments or len(segments) == 1:
            segments = self.split_by_length(text)
        
        # 播放每个分段
        for segment in segments:
            segment = segment.strip()
            if segment:
                print(f"播放分段: '{segment}'")
                self._speak_segment(segment)
                time.sleep(1)  # 分段之间间隔1秒

        print(f"播放结束。")
        self._speak_segment('播放结束')

    
    def split_by_punctuation(self, text):
        """按标点符号分段文本"""
        # 使用正则表达式按标点符号分段
        pattern = r'[，。！？；：,.!?;:]'
        segments = re.split(pattern, text)
        return [seg.strip() for seg in segments if seg.strip()]
    
    def split_by_length(self, text):
        """按长度分段文本"""
        # TTS模块单次播放不能超过32个字符
        max_length = 30
        segments = []
        for i in range(0, len(text), max_length):
            segment = text[i:i+max_length]
            if segment:
                segments.append(segment)
        return segments
    
    def _speak_segment(self, text):
        """实际执行TTS播放的内部函数"""
        if not text or len(text.strip()) == 0:
            print("警告: 尝试播放空文本")
            return
        
        # 确保每段不超过30个字符
        if len(text) > 30:
            text = text[:30]
            
        try:
            # 添加音量和发音方式控制
            self.tts.TTSModuleSpeak('[h0][v10]', text)
            # 给TTS足够的播放时间
            sleep_time = min(max(len(text) * 0.15, 0.8), 3)
            time.sleep(sleep_time)
        except Exception as e:
            print(f"TTS播放失败: {e}")
            print(traceback.format_exc())
            # 如果TTS失败，至少在控制台显示文本
            print(f"语音播报失败，文本内容: {text}")

    def run_once(self):
        """执行一次图像识别流程"""
        # 先播放提示音 - 使用安全的播放函数
        self.safe_speak("让我看看")
        time.sleep(1)
        
        # 捕获图像
        path = self.capture_image()
        if not path:
            self.safe_speak("拍照失败")
            return
        
        # 调用大模型
        self.safe_speak("正在识别")
        desc = self.describe_image(path)
        
        # 确保desc是字符串
        if desc is None:
            desc = "识别结果为空"
        
        print("识别结果:", desc)
        
        # 播报结果
        if desc == "识别失败" or desc == "API返回格式异常" or desc == "图像文件不存在":
            self.safe_speak("我没看清楚")
        else:
            self.safe_speak(desc)

    def run(self):
        print("语音唤醒已启动，等待语音指令…")
        try:
            while True:
                try:
                    data = self.asr.getResult()
                    if data == 2:
                        print(f'识别编号: {data}')
                        print("收到语音命令：这是什么")
                        self.run_once()
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
    vision = VoiceActivatedVision()
    vision.run()


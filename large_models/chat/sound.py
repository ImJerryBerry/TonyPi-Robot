from tts_client import *
import os
import time

API_KEY=""

def play(wav_file_name):
    """
    读取wav文件名，然后播放
    如果文件不存在或播放失败，会打印错误信息
    """
    try:
        if not os.path.exists(wav_file_name):
            print(f"错误：音频文件不存在: {wav_file_name}")
            return False
            
        print(f"播放音频: {wav_file_name}")
        prompt = 'aplay -t wav {} -q'.format(wav_file_name)
        result = os.system(prompt)
        
        if result != 0:
            print(f"警告：音频播放可能失败，返回码: {result}")
            return False
        return True
    except Exception as e:
        print(f"音频播放出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def speak(text):
    """
    将文字转为wav文件，然后使用play播放
    如果文本为空或转换/播放失败，会打印错误信息
    """
    if not text or text.strip() == "":
        print("错误：不能播放空文本")
        return False
        
    try:
        print(f"合成并播放文本: {text[:30]}{'...' if len(text) > 30 else ''}")
        tts_client = SimplifiedTTSClient(api_key=API_KEY)
        tts_client.synthesize(text=text, output_file="response.wav")
        
        # 等待文件生成完成
        max_wait = 10  # 最多等待10秒
        wait_time = 0
        while not os.path.exists("response.wav") and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            
        if not os.path.exists("response.wav"):
            print("错误：语音合成失败，未生成音频文件")
            return False
            
        return play("response.wav")
    except Exception as e:
        print(f"语音合成或播放出错: {e}")
        import traceback
        traceback.print_exc()
        return False


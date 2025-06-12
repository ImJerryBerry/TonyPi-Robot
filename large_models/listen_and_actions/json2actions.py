from llm_client import AlibabaLLMClient
import json
import sys
import time
import os
import re
import traceback

# 添加TonyPi路径以导入相关模块
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'TonyPi'))

# 导入执行动作所需的模块
import hiwonder.TTS as TTS
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
from ActionGroupDict import action_group_dict

class VoiceHelper:
    """语音播报助手，参考vlm_ud.py中的实现"""
    def __init__(self):
        self.tts = TTS.TTS()
    
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
                time.sleep(0.5)  # 分段之间间隔0.5秒

        print(f"播放结束。")

def execute_action_sequence(action_sequence, voice_helper):
    """
    按顺序执行动作序列
    
    Args:
        action_sequence: 包含动作序列的列表，每个动作是一个包含sequence_id和action_id的字典
        voice_helper: 语音助手实例
    """
    # 确保机器人处于站立状态
    print("初始化机器人姿态...")
    AGC.runActionGroup('stand')
    time.sleep(1)
    
    # 按顺序执行每个动作
    for action in sorted(action_sequence, key=lambda x: x['sequence_id']):
        action_id = action['action_id']
        sequence_id = action['sequence_id']
        
        try:
            # 获取动作名称
            action_name = action_group_dict[action_id]
            print(f"执行动作 {sequence_id}: {action_name} (ID: {action_id})")
            
            # 语音提示当前执行的动作
            voice_helper.safe_speak(f"第{sequence_id}个动作")
            
            # 执行动作
            AGC.runActionGroup(action_name, 1, True)
            time.sleep(0.5)  # 动作间短暂停顿
            
        except KeyError:
            print(f"警告: 未找到ID为 {action_id} 的动作")
            voice_helper.safe_speak(f"未知动作")
    
    # 执行完毕，回到站立姿态
    AGC.runActionGroup('stand')
    voice_helper.safe_speak("动作序列执行完毕")

def main(command_str):
    """
    主函数：处理用户命令，获取动作序列并执行
    
    Args:
        command_str: 用户的自然语言指令
    """
    # 初始化语音助手
    voice_helper = VoiceHelper()
    
    try:
        # 播报开始处理指令
        voice_helper.safe_speak("收到指令，正在处理")
        
        # 1. 初始化LLM客户端
        llm_client = AlibabaLLMClient(api_key="")
        
        # 2. 获取对用户自然语言指令的回复
        voice_helper.safe_speak("正在分析指令")
        result = llm_client.get_action_sequence(user_command=command_str)
        
        if result:
            print("成功从大模型获取解析结果：")
            pretty_result = json.dumps(result, indent=2, ensure_ascii=False)
            print(pretty_result)
            
            # 3. 语音反馈LLM的文本回复
            text_response = result['text_response']
            print(f"模型回复: {text_response}")
            voice_helper.safe_speak(text_response)
            
            # 4. 执行动作序列
            execute_action_sequence(result['action_sequence'], voice_helper)
            
        else:
            print("未能获取有效的解析结果。")
            voice_helper.safe_speak("我没有理解您的指令，请重新尝试")
            
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        print(traceback.format_exc())
        voice_helper.safe_speak("执行出错，请重试")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 从命令行参数获取指令
        command = " ".join(sys.argv[1:])
    else:
        # 默认测试指令
        command = "你好，请先原地踏步，然后来一个左勾拳和一个右勾拳，最后再鞠个躬。"
        
    print(f"执行指令: '{command}'")
    main(command)

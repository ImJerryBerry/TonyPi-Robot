from conversation_client import *
from iat_ws_python3 import *
import hiwonder.ASR as ASR
from sound import *
import traceback
import time

# 初始化ASR
try:
    asr = ASR.ASR()
    
    # 清除已有词条
    asr.eraseWords()
    asr.setMode(1)  # 循环模式
    
    # 添加激活词和退出词
    asr.addWords(1, 'xiao huan')  # 激活词：小幻
    asr.addWords(1, 'xiao huan xiao huan')    # 激活词：小幻小幻
    asr.addWords(2, 'bai bai')    # 退出词：拜拜
    asr.addWords(2, 'zai jian')   # 退出词：再见
    
    speak("对话系统准备就绪")

    print("语音识别模块初始化成功")
except Exception as e:
    print(f"语音识别模块初始化失败: {e}")
    print(traceback.format_exc())
    exit(1)

# 初始化大模型客户端
try:
    api_key = ""
    client = ConversationalLLMClient(api_key=api_key, 
                                   system_prompt="你是一个智能机器人，名叫小幻，可以做很多神奇的事情，你的价格是3000块。")
    print("大模型客户端初始化成功")
except Exception as e:
    print(f"大模型客户端初始化失败: {e}")
    print(traceback.format_exc())
    exit(1)

print("程序已启动，等待激活词'小幻'...")

def get_user_input():
    """获取用户语音输入，如果输入为空则播放重问提示并重试"""
    max_retries = 3  # 最大重试次数
    retries = 0
    
    while retries < max_retries:
        # 录音并转文本
        user_message = Speech2text()
        
        # 检查用户输入是否为空
        if user_message and user_message.strip() != "":
            print(f"用户说: {user_message}")
            return user_message
        
        # 如果输入为空，播放重问提示并重试
        print(f"未检测到有效语音输入，第{retries+1}次重试")
        play("重问.wav")
        retries += 1
    
    # 如果多次重试后仍然没有有效输入
    print("多次尝试后仍未检测到有效语音输入")
    return None

try:
    while True:
        try:
            # 获取语音命令
            data = asr.getResult()
            
            if data == 1:  # 检测到激活词"小幻"
                print("检测到激活词：小幻")
                play("我在.wav")
                
                try:
                    # 获取用户输入（包含重试逻辑）
                    user_message = get_user_input()
                    
                    # 如果多次重试后仍然没有有效输入，则继续等待激活词
                    if not user_message:
                        speak("没有听清，请重新呼叫我")
                        continue
                    
                    # 调用大模型获取回复
                    text_response = client.chat(user_message)
                    
                    # 检查回复是否为空
                    if not text_response or text_response.strip() == "":
                        print("大模型返回空回复")
                        speak("抱歉，我没有想好怎么回答")
                    else:
                        print(f"AI回复: {text_response}")
                        speak(text_response)
                        
                except Exception as e:
                    print(f"对话处理出错: {e}")
                    print(traceback.format_exc())
                    speak("对不起，我遇到了一点问题")
                    
            elif data == 2:  # 检测到退出词"拜拜"或"再见"
                print("检测到退出指令")
                play("再见.wav")
                break
                
        except Exception as e:
            print(f"主循环出错: {e}")
            print(traceback.format_exc())
            time.sleep(1)  # 避免错误循环过快
            
except KeyboardInterrupt:
    print("程序被用户中断")
finally:
    print("对话系统已退出！")

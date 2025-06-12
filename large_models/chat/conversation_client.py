import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse, Message
import json
from typing import List, Dict, Union

# =====================================================================
#  New Conversational Client Class
# =====================================================================

class ConversationalLLMClient:
    """
    用于与阿里云大语言模型进行多轮对话的客户端。
    此类会维护一个对话历史，使得模型能够根据上下文进行回复。
    """
    def __init__(self, api_key: str, model_name: str = dashscope.Generation.Models.qwen_turbo, system_prompt: str = None):
        """
        初始化对话客户端。

        :param api_key: 你的阿里云 Dashscope API Key。
        :param model_name: 要使用的模型名称，默认为 qwen_turbo。
        :param system_prompt: 给模型的系统级指令，用于设定其角色和行为。
        """
        dashscope.api_key = api_key
        self.model = model_name
        
        # 如果未提供 system_prompt，则使用一个默认的友好助手提示
        if system_prompt is None:
            system_prompt = "You are a helpful assistant. 你是一个乐于助人的AI助手。"

        # 初始化对话历史，并以系统提示作为第一条消息
        # 对话历史的格式遵循模型API的要求 (e.g., [{'role': 'system', 'content': '...'}])
        self.history: List[Dict[str, str]] = [{'role': 'system', 'content': system_prompt}]
        print(f"系统提示设定: {system_prompt}")

    def chat(self, user_input: str) -> Union[str, None]:
        """
        发送用户输入给大模型，并获取模型的回复。
        此方法会更新内部的对话历史。

        :param user_input: 用户的单轮输入字符串。
        :return: 模型生成的文本回复，或在失败时返回 None。
        """
        # 检查输入是否为空
        if not user_input or not isinstance(user_input, str) or user_input.strip() == "":
            print("错误：用户输入不能为空或非字符串类型。")
            return None

        # 1. 将用户的当前输入添加到对话历史中
        self.history.append({'role': 'user', 'content': user_input})
        
        print("\n--- 正在调用大模型（附带历史记录）---")
        try:
            # 2. 调用大模型，传入完整的对话历史
            # 注意：对于多轮对话，我们传递的是 `messages` 参数，而不是 `prompt`
            response: GenerationResponse = dashscope.Generation.call(
                model=self.model,
                messages=self.history,
                result_format='message',  # 请求返回消息格式，方便处理
                timeout=30  # 设置30秒超时
            )

            if response.status_code == 200:
                # 3. 提取模型的回复
                # `response.output.choices[0].message` 是一个包含 'role' 和 'content' 的字典
                if (hasattr(response, 'output') and 
                    hasattr(response.output, 'choices') and 
                    len(response.output.choices) > 0 and
                    'message' in response.output.choices[0]):
                    
                    assistant_message = response.output.choices[0].message
                    if 'content' in assistant_message:
                        assistant_response_text = assistant_message['content']
                        
                        # 检查回复是否为空
                        if not assistant_response_text or assistant_response_text.strip() == "":
                            print("警告：大模型返回了空回复")
                            return "抱歉，我现在无法回答这个问题。"

                        # 4. 将模型的回复也添加到对话历史中，以便下一轮对话使用
                        self.history.append(assistant_message)
                        
                        print("--- 大模型调用成功 ---")
                        return assistant_response_text
                    else:
                        print("错误：大模型回复中缺少content字段")
                else:
                    print("错误：大模型回复格式异常")
                    
                # 如果无法提取回复内容，返回一个友好的错误消息
                return "抱歉，我遇到了一些技术问题，无法正确回复。"
            else:
                print(f"大模型API调用失败。状态码: {response.status_code}")
                if hasattr(response, 'message'):
                    print(f"错误信息: {response.message}")
                # 如果调用失败，从历史记录中移除刚才添加的用户输入，以防污染后续对话
                self.history.pop()
                return "抱歉，我暂时无法回答，请稍后再试。"

        except Exception as e:
            print(f"与大模型通信时发生异常: {e}")
            import traceback
            traceback.print_exc()
            # 同样地，移除失败的用户输入
            if self.history and self.history[-1]['role'] == 'user':
                self.history.pop()
            return "抱歉，我遇到了网络或服务问题，请稍后再试。"
    
    def clear_history(self, system_prompt: str = None):
        """
        清空对话历史，可以重新开始一个新的对话。
        """
        # 保留系统提示或更新为新的系统提示
        original_system_prompt = self.history[0]
        if system_prompt:
             original_system_prompt = {'role': 'system', 'content': system_prompt}
        
        self.history = [original_system_prompt]
        print("对话历史已清空。")


# =====================================================================
#  模块化测试入口
# =====================================================================
if __name__ == "__main__":
    print("===== 正在测试 ConversationalLLMClient 模块 =====")
    
    try:
        # 请确保你已经设置了 API Key
        # 为了安全，建议使用环境变量，此处为演示目的直接写入
        api_key = ""

        if not api_key:
            raise ValueError("API Key not found. Please set your API key.")

        # 初始化对话客户端
        # 你可以自定义 system_prompt 来让AI扮演不同角色
        # a. 默认助手
        # client = ConversationalLLMClient(api_key=api_key)
        # b. 扮演莎士比亚风格的诗人
        prompt = "你叫小幻，是一个智能机器人，可以做各种有意思的事情，你的价格是3000人民币" 
        client = ConversationalLLMClient(api_key=api_key, system_prompt=prompt)

        print("\n--- 开始对话 (输入 'exit' 或 'quit' 来结束) ---")
        
        # 开启一个循环，模拟连续对话
        while True:
            user_message = input("You: ")
            
            if user_message.lower() in ['exit', 'quit']:
                print("--- 对话结束 ---")
                break
            
            # 调用 chat 方法获取回复
            ai_response = client.chat(user_message)
            
            if ai_response:
                print(f"AI: {ai_response}")

    except ValueError as ve:
         print(f"配置错误: {ve}")
    except Exception as e:
        print(f"\n测试过程中发生未知错误: {e}")

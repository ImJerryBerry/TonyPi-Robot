import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse
import json
from typing import Union

class AlibabaLLMClient:
    """
    用于调用阿里云大语言模型并解析结果的客户端。
    这个版本内置了固定的中文动作列表。
    """
    def __init__(self, api_key: str, model_name: str = dashscope.Generation.Models.qwen_turbo):
        dashscope.api_key = api_key
        self.model = model_name
        self.action_map = {
            '0': '立正', '1': '前进', '2': '后退', '3': '左移', '4': '右移',
            '5': '俯卧撑', '6': '仰卧起坐', '7': '左转', '8': '右转', '9': '挥手',
            '10': '鞠躬', '11': '下蹲', '12': '庆祝', '13': '左脚踢', '14': '右脚踢',
            '15': '咏春', '16': '左勾拳', '17': '右勾拳', '18': '左侧踢', '19': '右侧踢',
            '20': '前跌倒起立', '21': '后跌倒起立', '22': '扭腰', '23': '慢速立正',
            '24': '原地踏步', '35': '举重', '36': '跳舞'
        }

    def get_action_sequence(self, user_command: str) -> Union[dict, None]:
        """
        调用大模型，将自然语言指令转换为结构化的动作序列。
        """
        prompt = self._build_prompt(user_command)
        print("\n--- 构建的Prompt ---")
        print(prompt)
        print("--------------------")

        try:
            print("正在调用大模型...")
            response: GenerationResponse = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                result_format='json'
            )
            
            if response.status_code == 200:
                print("大模型调用成功！")

                # =======================================================
                #  核心修正点：清理并提取纯净的 JSON 字符串
                # =======================================================
                raw_text = response.output.text
                
                # 找到第一个 '{' 和最后一个 '}' 的位置
                json_start_index = raw_text.find('{')
                json_end_index = raw_text.rfind('}')

                if json_start_index != -1 and json_end_index != -1:
                    # 截取从第一个 '{'到最后一个 '}' 的所有内容
                    json_string = raw_text[json_start_index : json_end_index + 1]
                    
                    # 现在，我们解析这个纯净的JSON字符串
                    llm_output = json.loads(json_string)
                    return self._validate_and_parse(llm_output)
                else:
                    print(f"错误：在返回的文本中未找到有效的JSON对象。返回内容：\n{raw_text}")
                    return None
                # =======================================================

            else:
                print(f"大模型API调用失败。状态码: {response.status_code}")
                print(f"错误信息: {response.message}")
                return None
        except json.JSONDecodeError as e:
            # 专门捕获JSON解析错误，提供更清晰的反馈
            print(f"JSON解析失败: {e}")
            print(f"模型返回的原始文本: {response.output.text}")
            return None
        except Exception as e:
            print(f"调用大模型时发生异常: {e}")
            return None

    def _build_prompt(self, user_command: str) -> str:
        # ... (这部分代码无需修改，保持原样)
        action_list_str = "\n".join([f"- {name} (动作号: {num})" for num, name in self.action_map.items()])
        return f"""
        你是一个智能机器人助手。你的任务是将用户的自然语言指令，解析成一个标准化的动作序列。

        # 可用动作列表
        这是你能够执行的所有动作和它们对应的唯一“动作号”：
        {action_list_str}

        # 用户指令
        用户的指令是："{user_command}"

        # 你的任务
        1.  理解用户指令中的动作顺序，指令中可能包含重复的动作。
        2.  生成一段确认性的文本回复，用友好的语气复述你将要执行的动作顺序。例如："好的，收到指令，我将先...，再...，最后..."。标点符号分开的每一句话最多8个字。
        3.  创建一个JSON对象，其中包含这个文本回复和一个名为 "action_sequence" 的数组。
        4.  在 "action_sequence" 数组中，列出要执行的动作。每个动作都是一个包含 "sequence_id"（从1开始的执行序号）和 "action_id"（对应的动作号）的对象。

        # 输出格式要求
        请严格按照以下JSON格式返回，不要添加任何额外的解释或文字。
        {{
          "text_response": "好的，我将先执行A，再执行B。",
          "action_sequence": [
            {{
              "sequence_id": 1,
              "action_id": "动作号A"
            }},
            {{
              "sequence_id": 2,
              "action_id": "动作号B"
            }}
          ]
        }}
        注意，这里的action_id需要返回字符串形式的数字！！！
        """

    def _validate_and_parse(self, llm_output: dict) -> Union[dict, None]:
        # ... (这部分代码无需修改，保持原样)
        try:
            if "text_response" not in llm_output or "action_sequence" not in llm_output:
                print("错误：返回的JSON缺少 'text_response' 或 'action_sequence' 字段。")
                return None
            
            if not isinstance(llm_output["action_sequence"], list):
                print("错误：'action_sequence' 字段必须是一个列表。")
                return None

            print("返回的JSON格式验证通过。")
            return llm_output
        except Exception as e:
            print(f"解析和验证LLM输出时出错: {e}")
            return None

# =======================================================
#  模块化测试入口 (保持不变)
# =======================================================
if __name__ == "__main__":
    import os
    print("===== 正在独立测试 AlibabaLLMClient 模块 =====")
    test_command = "你好，请先原地踏步，然后来一个左勾拳和一个右勾拳，最后再鞠个躬。"
    try:
        api_key = ""

        if not api_key:
             raise ValueError("API Key not found. Please set DASHSCOPE_API_KEY environment variable.")
        print(f"测试指令: '{test_command}'")
        llm_client = AlibabaLLMClient(api_key=api_key)
        result = llm_client.get_action_sequence(user_command=test_command)
        print("\n===== 测试完成 =====")
        if result:
            print("成功从大模型获取解析结果：")
            pretty_result = json.dumps(result, indent=2, ensure_ascii=False)
            print(pretty_result)
        else:
            print("未能获取有效的解析结果。")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")

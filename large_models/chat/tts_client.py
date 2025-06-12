import websocket
import json
import uuid
import os
import time
import re

class SimplifiedTTSClient:
    """
    一个封装了复杂 WebSocket 流程的简化版文本转语音(TTS)客户端。
    """
    def __init__(self, api_key: str, uri: str = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"):
        if not api_key:
            raise ValueError("API Key cannot be empty.")
        self.api_key = api_key
        self.uri = uri
        self.ws = None
        self.text_to_speak = ""
        self.output_file = ""
        self.task_id = ""
        self.task_finished = False

    def synthesize(self, text: str, output_file: str = "response.mp3"):
        print(f"开始合成任务，文本: '{text[:30]}...' -> 输出文件: {output_file}")
        self.text_to_speak = text
        self.output_file = output_file
        self.task_id = str(uuid.uuid4())
        self.task_finished = False

        if os.path.exists(self.output_file):
            os.remove(self.output_file)
            print(f"已删除旧的输出文件: {self.output_file}")

        header = {"Authorization": f"bearer {self.api_key}"}
        self.ws = websocket.WebSocketApp(
            self.uri,
            header=header,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever()

        if self.task_finished and os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0:
            print(f"语音合成成功！音频文件已保存至: {self.output_file}")
        else:
            print("语音合成失败。未能生成有效的音频文件。")

    def _on_open(self, ws):
        print("WebSocket 已连接，正在发送任务配置...")
        run_task_cmd = {
            "header": {
                "action": "run-task",
                "task_id": self.task_id,
                "streaming": "duplex"  # 修正：与原始代码保持一致
            },
            "payload": {
                "task_group": "audio", "task": "tts", "function": "SpeechSynthesizer",
                "model": "cosyvoice-v2",
                "parameters": {
                    "text_type": "PlainText", "voice": "longshu_v2", "format": "wav",
                    "sample_rate": 22050, "volume": 100, "rate": 1, "pitch":1
                },
                "input": {}
            }
        }
        ws.send(json.dumps(run_task_cmd))

    def _on_message(self, ws, message):
        if isinstance(message, str):
            msg_json = json.loads(message)
            header = msg_json.get("header", {})
            event = header.get("event")

            if event == "task-started":
                print("服务器任务已启动，正在发送文本...")
                text_chunks = self._split_text(self.text_to_speak)
                if not text_chunks:
                    print("警告：没有有效的文本内容可以发送。")
                for chunk in text_chunks:
                    self._send_continue_task(chunk)
                self._send_finish_task()

            elif event == "task-finished":
                print("任务已完成。")
                self.task_finished = True
                self.ws.close()

            elif event == "task-failed":
                error_msg = msg_json.get("payload", {}).get("error_message", "未知错误")
                print(f"任务失败: {error_msg}")
                self.task_finished = False
                self.ws.close()
        else:
            with open(self.output_file, "ab") as f:
                f.write(message)
            print(f"收到音频数据，大小: {len(message)} 字节，已写入文件。")

    def _on_error(self, ws, error):
        print(f"WebSocket 出错: {error}")
        self.task_finished = False

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket 已关闭。")

    def _split_text(self, text: str) -> list:
        text = text.strip()
        if not text:
            return []
        chunks = re.split(r'([，。！？、,!?])', text)
        result = [chunks[i] + (chunks[i+1] if i+1 < len(chunks) else '') for i in range(0, len(chunks), 2) if chunks[i]]
        return [chunk for chunk in result if chunk.strip()]

    def _send_continue_task(self, text: str):
        cmd = {
            "header": {
                "action": "continue-task",
                "task_id": self.task_id,
                "streaming": "duplex"  # 修正：与原始代码保持一致
            },
            "payload": {"input": {"text": text}}
        }
        self.ws.send(json.dumps(cmd))
        print(f"已发送文本块: '{text}'")

    def _send_finish_task(self):
        print("所有文本块发送完毕，已发送结束指令。")
        cmd = {
            "header": {
                "action": "finish-task",
                "task_id": self.task_id,
                "streaming": "duplex"  # 修正：与原始代码保持一致
            },
            # 核心修正：payload 必须是 {"input": {}} 而不是 {}
            "payload": {
                "input": {}
            }
        }
        self.ws.send(json.dumps(cmd))

# =====================================================================
#  示例使用方式
# =====================================================================
if __name__ == "__main__":
    try:
        # 请确保您已配置好 API Key
        API_KEY = ""
    except KeyError:
        print("错误: 请设置 DASHSCOPE_API_KEY 环境变量或在代码中直接提供您的 API Key。")
        exit()

    tts_client = SimplifiedTTSClient(api_key=API_KEY)
    text_to_speak = "抱歉，我没有听清楚你在说什么，可以再说一边吗？"
    tts_client.synthesize(text=text_to_speak, output_file="重问.wav")

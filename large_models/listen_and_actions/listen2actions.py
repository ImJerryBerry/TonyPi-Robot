from iat_ws_python3 import *
from json2actions import *

# 1. 录音，获得字符串
command_str = Speech2text()

print(command_str)

# 2. 发送请求，获得动作序列,执行动作序列
main(command_str)

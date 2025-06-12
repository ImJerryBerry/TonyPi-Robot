#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TonyPi/')

import time
from ActionGroupDict import *
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.Board as Board
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle

# 语音控制初始化
servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

try:
    asr = ASR.ASR()
    tts = TTS.TTS()

    asr.eraseWords()
    asr.setMode(2)  # 口令模式

    # 口令
    asr.addWords(1, 'kai shi')  # 激活词：开始

    # 动作指令绑定
    asr.addWords(2, 'wang qian zou')
    asr.addWords(2, 'qian jin')
    asr.addWords(2, 'zhi zou')
    asr.addWords(3, 'wang hou tui')
    asr.addWords(4, 'xiang zuo yi')
    asr.addWords(5, 'xiang you yi')
    asr.addWords(6, 'fu wo cheng')
    asr.addWords(7, 'yang wo qi zuo')
    asr.addWords(8, 'zuo zhuan')
    asr.addWords(9, 'you zhuan')
    asr.addWords(10, 'hui shou')
    asr.addWords(11, 'ju gong')
    asr.addWords(12, 'xia dun')
    asr.addWords(13, 'qing zhu')
    asr.addWords(14, 'zuo jiao ti')
    asr.addWords(15, 'you jiao ti')
    asr.addWords(16, 'yong chun')
    asr.addWords(17, 'zuo gou quan')
    asr.addWords(18, 'you gou quan')
    asr.addWords(19, 'zuo ce ti')
    asr.addWords(20, 'you ce ti')
    asr.addWords(21, 'qian qi li')
    asr.addWords(22, 'hou qi li')
    asr.addWords(23, 'niu yao')
    asr.addWords(24, 'li zheng')
    asr.addWords(25, 'ta bu')

    # 舵机初始化
    data = asr.getResult()
    Board.setPWMServoPulse(1, 1500, 500)
    Board.setPWMServoPulse(2, servo_data['servo2'], 500)
    AGC.runActionGroup('stand')
    action_finish = True
    tts.TTSModuleSpeak('[h0][v10][m3]', '我准备好了')

    print('''当前为口令模式，每次说指令前需先说“开始”来激活语音识别
【语音指令说明】：
2 : 往前走 / 前进 / 直走         -> go_forward
3 : 往后退                       -> back_fast
4 : 向左移                       -> left_move_fast
5 : 向右移                       -> right_move_fast
6 : 俯卧撑                       -> push_ups
7 : 仰卧起坐                     -> sit_ups
8 : 左转                         -> turn_left
9 : 右转                         -> turn_right
10: 挥手                         -> wave
11: 鞠躬                         -> bow
12: 下蹲                         -> squat
13: 庆祝                         -> chest
14: 左脚踢                       -> left_shot_fast
15: 右脚踢                       -> right_shot_fast
16: 永春                         -> wing_chun
17: 左勾拳                       -> left_uppercut
18: 右勾拳                       -> right_uppercut
19: 左侧踢                       -> left_kick
20: 右侧踢                       -> right_kick
21: 前跌倒起立                   -> stand_up_front
22: 后跌倒起立                   -> stand_up_back
23: 扭腰                         -> twist
24: 立正                         -> stand_slow
25: 原地踏步                     -> stepping
''')

    time.sleep(2)

except Exception as e:
    print('传感器初始化出错:', e)

# 主控制循环
while True:
    data = asr.getResult()
    if data:
        print(f'识别编号: {data}')
        try:
            action_name = action_group_dict[str(data - 1)]
            print(f'执行动作: {action_name}')
            tts.TTSModuleSpeak('', '好的')
            AGC.runActionGroup(action_name, 1, True)
        except KeyError:
            print(f'无对应动作: {data - 1}')
            tts.TTSModuleSpeak('', 'Unknown Command')
    time.sleep(0.01)


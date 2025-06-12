#!/usr/bin/python3
# coding=utf8

import os
import sys

# 添加TonyPi路径
sys.path.append('/home/pi/TonyPi/')

# 导入猜拳游戏模块
from rps_game import RPSGame

if __name__ == '__main__':
    print("启动石头剪刀布猜拳游戏...")
    game = RPSGame()
    game.run() 
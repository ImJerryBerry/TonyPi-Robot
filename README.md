# 基于TonyPi和大模型的智能机器人

## 项目概述

本项目为TonyPi人形机器人开发了一系列功能扩展模块，涵盖基础感知、视觉识别、语音交互和大模型集成等多个方面。

## 项目结构

```
/TonyPi-Robot
├── ActionGroups/               # 动作组列表
│
├── Functions/                  # 基础功能模块
│   ├── ASRControl.py           # 语音控制动作
│   ├── ColorDetectAndTTS.py    # 颜色识别
│   ├── ColorFollow.py          # 颜色跟踪
│   ├── ObjectDetection.py      # 物体检测
│   └── README_*.md             # 各功能说明文档
│
├── large_models/               # 大模型集成功能
│   ├── chat/                   # 大语言模型交互式对话
│   ├── listen_and_actions/     # 语音大模型控制动作
│   ├── RPS/                    # 视觉大模型猜拳游戏
│   ├── speech_pkg/             # speech软件包
│   └── VLM/                    # 视觉大模型识别景色
│
├── models/                     # 物体检测功能所需的模型文件夹
│
└── README.md                   # 项目总体说明
```

## 功能模块介绍

### 基础功能模块

1. **语音控制动作** (`ASRControl.py`)
   - 通过语音命令控制机器人执行预设动作
   - [详细文档](Functions/README_ASRControl.md)

2. **颜色识别** (`ColorDetectAndTTS.py`)
   - 实时识别红、绿、蓝三色并进行语音播报
   - [详细文档](Functions/README_ColorDetectAndTTS.md)

3. **颜色跟踪** (`ColorFollow.py`)
   - 实现机器人对特定颜色物体的跟踪功能
   - [详细文档](Functions/README_Follow.md)

4. **物体检测** (`ObjectDetection.py`)
   - 使用MobileNet SSD识别20种常见物体
   - [详细文档](Functions/README_ObjectDetection.md)

### 大模型集成功能

1. **大语言模型交互式对话** (`chat/`)
   - 实现自然、流畅的语音对话交互
   - [详细文档](large_models/chat/README.md)

2. **语音大模型控制动作** (`listen_and_actions/`)
   - 通过自然语言指令控制机器人执行动作序列
   - [详细文档](large_models/listen_and_actions/README.md)

3. **视觉大模型猜拳游戏** (`RPS/`)
   - 利用视觉大模型识别手势实现人机猜拳
   - [详细文档](large_models/RPS/README.md)

4. **视觉大模型识别景色** (`VLM/`)
   - 利用视觉大模型分析场景内容
   - [详细文档](large_models/README_VLM.md)

## 环境配置

### 基本硬件

- **TonyPi人形机器人**：项目的基础硬件平台
- **树莓派4B**：搭载在TonyPi上的主控制器
- **摄像头模块**：用于视觉识别功能

### 硬件连接

- 必备：摄像头、ASR模块、TTS模块
- 可选：扬声器、麦克风

### 软件需求

- **操作系统**：Raspberry Pi OS
- **Python**：Python 3.7.3

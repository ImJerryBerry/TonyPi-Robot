# 模型文件

## 目录说明
本目录包括物体检测功能需要调用的模型相关的文件。

使用前请确保`../models`文件夹内有模型相关的文件：
1. `MobileNetSSD_deploy.prototxt`
2. `MobileNetSSD_deploy.caffemodel`

如果没有上述文件，可前往[百度网盘](https://pan.baidu.com/s/15U78VMT5qYJih_ba-IbJMQ)或[Github](https://github.com/chuanqi305/MobileNet-SSD)下载，网盘提取码：`whut`。

如果没有模型文件，物体检测功能的程序会尝试使用OpenCV内置的人脸检测器作为备用方案。
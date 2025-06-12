#!/usr/bin/env python3
# encoding: utf-8
# @Author: Aiden
# @Date: 2025/02/21
import re
import json
import time
import serial

class WonderEchoPro:
    WAKEUP = b'\xaa\x55\x03\x00\xfb'
    SLEEP = b'\xaa\x55\x02\x00\xfb'
    def __init__(self, port):
        self.serialHandle = serial.Serial(None, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=0.02)
        self.serialHandle.rts = False
        self.serialHandle.dtr = False
        self.serialHandle.setPort(port)
        self.serialHandle.open()

    def start(self):
        while self.serialHandle.in_waiting > 0:  # 只要缓冲区有数据，就一直读取并丢弃
            self.serialHandle.read(self.serialHandle.in_waiting)

    def wakeup(self):
        recv_data = self.detect()
        if recv_data == self.WAKEUP:
            return True
        else:
            return False

    def detect(self):
        return self.serialHandle.read(5)

    def exit(self):
        self.serialHandle.close()

class CircleMic:
    def __init__(self, port='/dev/ttyCH341USB0', awake_word='xiao3 huan4 xiao3 huan4', mic_type='mic6_circle',
                 enable_setting=False):
        self.serialHandle = serial.Serial(None, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=0.02)
        self.serialHandle.rts = False
        self.serialHandle.dtr = False
        self.serialHandle.setPort(port)
        self.serialHandle.open()
        self.running = True
        self.key_type = r"{\"code.*?\"}"
        self.pattern = re.compile(r"{\"content.*?aiui_event\"}")
        
        if enable_setting:
            self.switch_mic(mic_type)
            self.set_wakeup_word(awake_word)

    # 麦克风阵列切换
    def switch_mic(self, mic="mic6_circle"):
        # mic：麦克风阵列类型，mic4：线性4麦，mic6：线性6麦， mic6_circle：环形6麦
        param = {
            "type": "switch_mic",
            "content": {
                "mic": "mic6_circle"
            }
        }
        param['content']['mic'] = mic
        header = [0xA5, 0x01, 0x05]
        res = self.send(header, param)
        if res is not None:
            pattern = re.compile(self.key_type)
            m = re.search(pattern, str(res))
            if m is not None:
                m = m.group(0)
                if m is not None:
                    return m

        return False

    # 获取版本信息
    def get_setting(self):
        param = {
            "type": "version"
        }

        header = [0xA5, 0x01, 0x05]
        res = self.send(header, param)
        if res is not None:
            pattern = re.compile(self.key_type)
            m = re.search(pattern, str(res))
            if m is not None:
                m = m.group(0)
                if m is not None:
                    return m

        return False

    # 唤醒词更换（浅定制）
    def set_wakeup_word(self, str_pinyin="xiao3 huan4 xiao3 huan4"):
        # 参数为中文拼音
        # 更多参数请参考https://aiui.xfyun.cn/doc/aiui/3_access_service/access_hardware/r818/protocol.html
        param = {
            "type": "wakeup_keywords",
            "content": {
                "keyword": "xiao3 huan4 xiao3 huan4",
                "threshold": "400"
            }
        }

        param['content']['keyword'] = str_pinyin
        header = [0xA5, 0x01, 0x05]
        print('\033[1;32m%s\033[0m' % 'setting wakeup keywords need about 30s')
        print('\033[1;32m%s\033[0m' % 'setting ......')
        self.send(header, param)
        while time.time() - self.start_time < 30:
            time.sleep(0.1)

    # 计算校验和
    def calculate_checksum(self, bytes_list):
        checksum = sum(bytes_list) & 0xFF
        checksum = (~checksum + 1) & 0xFF
        return checksum

    # 数据串口发送
    def send_data(self, header, args):
        packet = header

        data = bytes(json.dumps(args), encoding="utf8")

        length = len(data)
        low_length = int(length & 0xFF)
        high_length = int(length >> 8)

        packet.extend([low_length, high_length])
        packet.extend([0x00, 0x00])

        packet.extend(data)
        checksum = self.calculate_checksum(packet)
        packet.append(checksum)

        self.serialHandle.write(packet)  # 发送主控消息

    # 发送数据
    def send(self, header, args):
        self.serialHandle.write([0xa5, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0xa5, 0x00, 0x00, 0x00, 0xb0])  # 发送握手请求
        while True:
            result = None
            recv_data = self.serialHandle.read()
            header_ = [b'\xa5', b'\x01', b'\xff']
            if recv_data == header_[0]:
                recv_data = self.serialHandle.read()
                if recv_data == header_[1]:
                    recv_data = self.serialHandle.read()
                    if recv_data == header_[2]:
                        recv_data = self.serialHandle.read(4)
                        self.serialHandle.read((recv_data[1] << 8 | recv_data[0]) + 1)
                        self.send_data(header, args)
                        self.start_time = time.time()
                        break

                    else:  # 没有收到确认
                        recv_data = self.serialHandle.read(4)
                        self.serialHandle.read((recv_data[1] << 8 | recv_data[0]) + 1)

                        time.sleep(0.1)
                        self.serialHandle.write(
                            [0xa5, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0xa5, 0x00, 0x00, 0x00, 0xb0])  # 继续发送发送握手请求

        result = None
        while True:
            recv_data = self.serialHandle.read()
            header_ = [b'\xa5', b'\x01', b'\x04']
            if recv_data == header_[0]:
                recv_data = self.serialHandle.read()
                if recv_data == header_[1]:
                    recv_data = self.serialHandle.read()
                    if recv_data == header_[2]:
                        recv_data = self.serialHandle.read(4)
                        result = self.serialHandle.read((recv_data[1] << 8 | recv_data[0]) + 1)
                        break
        return result

    def val_map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # 检测是否唤醒以及唤醒对应角度
    def wakeup(self):
        angle = False
        recv_data = self.serialHandle.read()
        # print(recv_data)
        if recv_data == b'\xa5':
            recv_data = self.serialHandle.read()
            if recv_data == b'\x01':
                recv_data = self.serialHandle.read()
                if recv_data == b'\x04':
                    recv_data = self.serialHandle.read(4)
                    result = self.serialHandle.read((recv_data[1] << 8 | recv_data[0]) + 1)
                    if b'content' in result:
                        m = re.search(self.pattern, str(result).replace('\\', ''))
                        if m is not None:
                            m = m.group(0).replace('"{"', '{"').replace('}"', '}')
                            if m is not None:
                                angle = int(json.loads(m)['content']['info']['ivw']['angle'])
                                angle = self.val_map(angle, 0, 360, 360, 0) + 240  # 和圆形兼容
                                if angle >= 360:
                                    angle -= 360
                                return int(angle)
        return angle

    def start(self):
        while self.serialHandle.in_waiting > 0:  # 只要缓冲区有数据，就一直读取并丢弃
            self.serialHandle.read(self.serialHandle.in_waiting)

    def exit(self):
        self.serialHandle.close()

if __name__ == '__main__':
    kws = CircleMic('/dev/ring_mic', 'xiao3 huan4 xiao3 huan4', 'mic6_circle', False)
    kws.start()
    print('start')
    while True:
        if kws.wakeup():
            print('wakeup')
        time.sleep(0.02)

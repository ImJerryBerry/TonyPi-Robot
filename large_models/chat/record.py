import numpy as np
import pyaudio
import wave
import os


def listen():
    CHUNK = 256
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = os.path.join(os.getcwd(), './Record.wav')
    print(WAVE_OUTPUT_FILENAME)
    # return
    mindb = 800  # 最小声音，大于则开始录音，否则结束
    delayTime = 5  # 小声1.3秒后自动终止
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    # snowboydecoder.play_audio_file()
    print("开始!计时")

    frames = []
    flag = False  # 开始录音节点
    stat = True  # 判断是否继续录音
    stat2 = False  # 判断声音小了

    tempnum = 0  # tempnum、tempnum2、tempnum3为时间
    tempnum2 = 0

    while stat:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        audio_data = np.frombuffer(data, dtype=np.short)
        temp = np.max(audio_data)
        if temp > mindb and flag == False:
            flag = True
            tempnum2 = tempnum

        if flag:

            if (temp < mindb and stat2 == False):
                stat2 = True
                tempnum2 = tempnum
            if (temp > mindb):
                stat2 = False
                tempnum2 = tempnum

            if (tempnum > tempnum2 + delayTime * 15 and stat2 == True):
                if (stat2 and temp < mindb):
                    stat = False
                else:
                    stat2 = False


        # 显示音量和时刻
        print(str(temp) + "   " + str(tempnum))
        tempnum = tempnum + 1
        if tempnum > 1500:
            stat = False
    print("录音结束")

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

if __name__ == '__main__':
    listen()
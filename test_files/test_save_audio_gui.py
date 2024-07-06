import sys
import pyaudio
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
import wave

# 设置音频流的数据块大小
CHUNK = 1024
# 设置音频流的格式为16位整型，也就是2字节
FORMAT = pyaudio.paInt16
# 设置音频流的通道数为1
CHANNELS = 1
# 设置音频流的采样率为16KHz
RATE = 16000


# 定义一个录音的线程类
class RecordThread(QThread):
    record_signal = pyqtSignal()

    def __init__(self, rate, chunk, format, channels, outfilepath):
        super().__init__()
        self.rate = rate
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.outfilepath = outfilepath
        self.is_recording = False

    def run(self):
        self.is_recording = True
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        with wave.open(self.outfilepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)

            print('Recording...')

            while self.is_recording:
                data = stream.read(self.chunk)
                wf.writeframes(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            print('Recording finished.')

    def stop_recording(self):
        self.is_recording = False


# 创建一个简单的窗口类
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.button = QPushButton('Start Recording', self)
        self.button.clicked.connect(self.toggle_recording)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.thread = RecordThread(RATE, CHUNK, FORMAT, CHANNELS, 'output1.wav')
        self.thread.record_signal.connect(self.update_status)

    def toggle_recording(self):
        if not self.thread.isRunning():
            self.thread.start()
            self.button.setText('Stop Recording')
        else:
            self.thread.stop_recording()
            self.thread.wait()
            self.button.setText('Start Recording')

    def update_status(self):
        if not self.thread.is_recording:
            self.button.setText('Start Recording')


# 主函数
def main():
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

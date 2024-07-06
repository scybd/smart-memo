import pyaudio
import sys
import wave
import os
from pathlib import Path
from datetime import datetime, timedelta

from PyQt5.QtCore import QThread, pyqtSignal, QStringListModel, QTimer, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStatusBar, QVBoxLayout
from PyQt5.QtGui import QIcon

import ai_tools
import tools
import xf_tools
from main_ui import Ui_Form_memo


basedir = os.path.dirname(__file__)     # 本文件路径


class MainForm(QWidget, Ui_Form_memo):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.createTrayIcon()
        self.ai_thread = AIThread()     # 实例化 AI 线程对象
        audio_file_path = os.path.expanduser('~/.SmartMemo/data.txt')
        self.audio_thread = AudioThread(audio_file_path)   # 实例化语音处理线程对象
        self.model = QStringListModel(self)     # 用于 listView 显示
        self.init_interface()

        self.pushButton_extract.clicked.connect(self.slot_extract)   # 点击提取按钮
        self.pushButton_clearall.clicked.connect(self.slot_clearall)    # 点击清空按钮
        self.pushButton_audio_input.clicked.connect(self.slot_audio)    # 点击语音输入按钮

        self.signal_tasks_monitor = QTimer()    # 定时检测 listView_list_output 中的事件时间，提前15分钟提醒
        self.signal_tasks_monitor.timeout.connect(self.function_tasks_monitor)
        self.signal_tasks_monitor.start(10000)  # 10s
        self.reminded_tasks = []    # 存储已经提醒过的事件

    def closeEvent(self, event):
        # 重写closeEvent方法，点击关闭按钮时隐藏窗口而不是退出程序
        self.hide()
        event.ignore()

    def createTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join(basedir, 'cover.png')))  # 设置托盘图标
        self.tray_icon.show()

        self.menu = QMenu()
        self.show_action = self.menu.addAction('显示')
        self.show_action.triggered.connect(self.showNormal)  # 连接信号显示窗口
        self.quit_action = self.menu.addAction('退出')
        self.quit_action.triggered.connect(QCoreApplication.instance().quit)

        self.tray_icon.setContextMenu(self.menu)

    def init_interface(self):
        # 读取 data.txt 中的数据显示在 listView 上
        self.model.setStringList([])
        formatted_events = tools.read_data()
        self.model.setStringList(formatted_events)
        self.listView_list_output.setModel(self.model)
        # 读取 api_key.txt 中的数据
        self.lineEdit_key.setText(tools.read_api_key())

    def slot_extract(self):
        # 获取用户输入的文本和api_key
        user_input = self.plainTextEdit_text_input.toPlainText()
        api_key = self.lineEdit_key.text()
        # 启动AI线程，并将用户输入的文本作为参数传递
        self.ai_thread.start(user_input, api_key=api_key)
        # AI线程完成信号连接到显示文本函数
        self.ai_thread.signal_text_output.connect(self.slot_show_list)
        # 保存api_key
        api_file_path = os.path.expanduser('~/.SmartMemo/api_key.txt')
        with open(api_file_path, 'w', encoding='utf-8') as file:
            file.write(self.lineEdit_key.text())

    def slot_show_list(self, text):
        self.model.setStringList([])    # 清空显示内容
        flag, formatted_events = tools.str2list(text)
        if flag:
            self.model.setStringList(formatted_events)
        else:
            self.model.setStringList(['我只是个备忘录...'])
        self.listView_list_output.setModel(self.model)

    def slot_clearall(self):
        self.model.setStringList([])
        self.listView_list_output.setModel(self.model)
        self.plainTextEdit_text_input.clear()
        data_file_path = os.path.expanduser('~/.SmartMemo/data.txt')
        os.remove(data_file_path)

    def slot_audio(self):
        if not self.audio_thread.is_recording:
            self.pushButton_audio_input.setStyleSheet('QPushButton {background-color: green;}')
            self.audio_thread.start()   # 启动语音处理线程
            self.audio_thread.signal_audio_to_text.connect(self.slot_show_text)
        else:
            self.audio_thread.stop_recording()
            self.audio_thread.wait()
            self.pushButton_audio_input.setStyleSheet('')

    def slot_show_text(self, text):
        # 显示语音转文字的内容
        self.plainTextEdit_text_input.clear()
        self.plainTextEdit_text_input.setPlainText(text)

    def function_tasks_monitor(self):
        rows = self.model.rowCount()
        for row in range(rows):
            text = self.model.data(self.model.index(row, 0), Qt.DisplayRole)
            task_time = tools.parse_datetime_from_text(text)
            if task_time:
                now = datetime.now()
                reminder_time = task_time - timedelta(minutes=15)
                if reminder_time <= now <= task_time and text not in self.reminded_tasks:
                    self.reminded_tasks.append(text)
                    print("即将到来的事件：", text)
                    tray_icon = QSystemTrayIcon(QIcon("path/to/icon"), app)
                    tray_icon.show()
                    tray_icon.showMessage("智能备忘录提醒!", text, QIcon("path/to/icon"), 4000)  # 指定显示时间为4s


class AIThread(QThread):
    signal_text_output = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.api_key = None
        self.user_input = None

    def start(self, user_input, api_key):
        # 保存用户输入的文本
        self.user_input = user_input
        self.api_key = api_key
        super().start()

    def run(self):
        res = ai_tools.call_with_messages(self.user_input, self.api_key)
        self.signal_text_output.emit(res)


class AudioThread(QThread):
    signal_audio_to_text = pyqtSignal(str)

    def __init__(self, output_file_path):
        super().__init__()
        self.rate = 16000   # 设置音频流的采样率为16KHz
        self.chunk = 1024   # 设置音频流的数据块大小
        self.format = pyaudio.paInt16   # 设置音频流的格式为16位整型，也就是2字节
        self.channels = 1   # 设置音频流的通道数为1
        self.output_file_path = output_file_path
        self.is_recording = False

    def run(self):
        self.is_recording = True
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        with wave.open(self.output_file_path, 'wb') as wf:
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
        self.signal_audio_to_text.emit(xf_tools.audio_to_text())

    def stop_recording(self):
        self.is_recording = False


if __name__ == "__main__":
    tools.app_init(Path(os.path.expanduser('~/.SmartMemo/data.txt')))
    tools.app_init(Path(os.path.expanduser('~/.SmartMemo/audio.wav')))
    tools.app_init(Path(os.path.expanduser('~/.SmartMemo/api_key.txt')))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir, 'cover.png')))
    w = MainForm()
    w.show()
    sys.exit(app.exec_())

import ast
import re
import os
from datetime import datetime


def read_data():
    """
    读取 data.txt 中的内容用于 listView 的初始显示
    """
    data_file_path = os.path.expanduser('~/.SmartMemo/data.txt')
    with open(data_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 准备一个空列表来存储格式化后的字符串
    formatted_events = []

    for line in lines:
        # 去除每行的首尾空白字符，包括换行符
        event_line = line.strip()

        event_str, event_time_str = event_line.split(' ', 1)

        year, month, day, hour, minute = map(int, event_time_str.split())
        formatted_datetime = "{}年{}月{}日{}时{}分".format(year, month, day, hour, minute)

        formatted_event = "{} {}".format(event_str, formatted_datetime)
        formatted_events.append(formatted_event)

    return formatted_events


def str2list(raw_string):
    """
    将大模型的输出转换为列表方便显示，同时保存到 data.txt 中
    :param raw_string: 大模型原始字符串类型的输出
    :return: 事项时间列表
    """
    # 大模型的输出可能包含无用的汉字等，使用正则表达式提取中括号及其内容
    match = re.search(r'\[.*\]', raw_string)

    if match:
        # 提取匹配的列表字符串
        raw_string = match.group(0)

        if len(raw_string) == 2:    # 只有[]
            return False, []

        # 将字符串转换成Python对象
        events = ast.literal_eval(raw_string)

        # 准备一个空列表来存储格式化后的字符串
        formatted_events = []

        # 打开 data.txt
        data_file_path = os.path.expanduser('~/.SmartMemo/data.txt')
        with open(data_file_path, 'w', encoding='utf-8') as file:
            # 遍历转换后的列表
            for event in events:
                # 找到字符串和元组
                event_str = next(filter(lambda x: isinstance(x, str), event))
                datetime_tuple = next(filter(lambda x: isinstance(x, tuple), event))

                # 格式化时间
                formatted_datetime = "{}年{}月{}日{}时{}分".format(*datetime_tuple)

                # 组合事件描述和格式化的日期时间
                formatted_event = "{} {}".format(event_str, formatted_datetime)

                # 将格式化后的字符串添加到列表中
                formatted_events.append(formatted_event)

                file.write(f"{event_str} {' '.join(map(str, datetime_tuple))}\n")

        return True, formatted_events

    else:
        return False, []


def read_api_key():
    """
    读取 api_key.txt 中的密钥设置为默认密钥
    """
    api_file_path = os.path.expanduser('~/.SmartMemo/api_key.txt')
    with open(api_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if len(lines) == 1:
            return lines[0].strip()


def parse_datetime_from_text(text):
    """
    使用正则表达式匹配文本中的日期和时间
    :param text:
    :return: datetime if it exists
    """
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时(\d{1,2})分", text)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        return datetime(year, month, day, hour, minute)
    return None


def app_init(file_path):
    """
    软件开始运行时执行，判断"~/.SmartMemo/"中是否数据文件，若无则新建
    :param file_path:
    :return: None
    """
    if not file_path.exists():
        # 若文件不存在，则创建文件和目录
        os.makedirs(file_path.parent, exist_ok=True)
        file_path.touch()
        print(f'{file_path} has been created.')
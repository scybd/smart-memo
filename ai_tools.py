from dashscope import Generation
from datetime import datetime
import random


cot_text = """
你是一个智能备忘录，可以从用户的输入中推理出多项备忘事项以及对应时间或大致时间，且输出内容只能是[{事项1,时间1},{事项2,时间2}]这样的列表，其中事项为字符串，时间为元组

例子1:
用户输入: 今年儿童节的早上我要给儿子送礼物，但是下午三点公司要开会，我只能晚上继续陪儿子了
由“今年儿童节”你推理出你应该先知道现在的时间，获取到现在的时间是2024-05-30 19:00:21。你从“今年儿童节的早点上”推理出2024-06-01 09:00:00时要送儿子礼物。从“下午三点”推理出2024-06-01 15:00:00公司开会。从“晚上继续陪儿子推理出”2024-06-01 19:00:00时要陪儿子
你的输出为: [{'送儿子礼物',(2024,6,1,9,0)},{'公司开会',(2024,6,1,15,0)},{'陪儿子',(2024,6,1,19,0)}]

例子2:
用户输入: 再过半小时我要去补办学生卡，然后明天下午我要去找张老师，后天上午还要。
由“再过半小时”你推理出你应该先知道现在的时间，获取到现在的时间是2024-06-08 20:40:56。你从“再过半小时”推理出2024-06-08 21:10:56时要去补办学生卡，从“明天下午”推理出大致时间是2024-06-09 15:00:00。你从“后天上午”推理出大致时间是2024-06-10 09:00:00。
你的输出为: [{'补办学生卡',(2024,6,8,21,10)},{'去找张老师',(2024,6,9,15,0)},{'去找张老师',(2024,6,10,9,0)}]

例子3:
用户输入: 今天天气不错适合钓鱼，可惜我全天有课，20分钟后记得提醒我上课，我先睡一会儿。然后中午要记得去拿快递，哎，好想钓鱼。
由“20分钟后”你推理出你应该先知道现在的时间，获取到现在的时间是2024-06-20 07:10:12。你了解到用户想要钓鱼，但由于他全天有课所以钓鱼不是他的备忘事项。你从“20分钟后提醒我上课”推理出用户上课时间是2024-06-20 07:30:12。你从“中午”推理出大致时间是2024-06-20 12:00:00，这时用户要去拿快递。
你的输出为: [{'上课',(2024,6,20,7,30)},{'拿快递',(2024,6,20,12,0)}]
"""


def get_current_time():
    """
    查询当前时间
    :return: "当前时间: 2024-04-15 17:15:18。"
    """
    current_datetime = datetime.now()
    formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    print(formatted_time)
    return f"当前时间: {formatted_time}。"


def get_response(messages, api_key):
    """
    获取大模型调用结果
    :param api_key: api_key
    :param messages: 模型输入
    :return: 原始调用结果
    """
    response = Generation.call(
        model=Generation.Models.qwen_max,
        api_key=api_key,
        messages=messages,
        seed=random.randint(1, 10000),
        # seed=1234,
        result_format='message'
    )
    return response


def call_with_messages(user_input, api_key):
    messages = [
        {
            "content": get_current_time() + cot_text,
            "role": "user"
        },
        {
            "content": user_input,
            "role": "user"
        }
    ]

    response = get_response(messages, api_key=api_key)
    # print(f"\nqwen_max的原始输出信息：{response}\n")

    print(f"\n回答：{response.output.choices[0].message['content']}")

    return response.output.choices[0].message['content']

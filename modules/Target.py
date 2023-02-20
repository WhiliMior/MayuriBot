import codecs
import os
import random
import re

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    ParamMatch,
    RegexResult,
    RegexMatch,
    Twilight,
    SpacePolicy,
)
from graia.ariadne.model import Group, Friend
from graia.ariadne.util.saya import listen, dispatch

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.tar {目标数值} 固定数值
.tar {等级} {难度} 计算数值
.tar {等级}d 随机难度
"""


def input_error():
    return f'指令错误×\n' \
           f'请正确输入.tar指令!'


def type_friend():
    return '目标数值指令仅在群聊使用×'


def tar_set(target_value):
    return f'已设定目标数值为{target_value}√'


def tar_ran(random_number, target_value):
    return f'随机难度：{random_number}\n' \
           f'已设定目标数值为{target_value}√'


def tar_is(target_value):
    return f'目标数值: {target_value}'


def tar_none():
    return '未设定目标数值×'


# 监听指令并回复
regular_expression = regex.Target
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Target(app: Ariadne, sender: Sender, target: Target,
                 command1: RegexResult, command2: RegexResult):
    # 判断消息来源:群聊or私聊? 提取群聊发送者qq
    if isinstance(sender, Friend):
        notice = type_friend()
    elif isinstance(sender, Group):
        g = game_data.Group(sender.id)
        path_group_folder = g.path_group_folder
        path_group_file_tar = g.path_group_file_tar

        def write_tar(value):
            if not os.path.exists(path_group_folder):
                os.makedirs(path_group_folder)
            f = codecs.open(path_group_file_tar, 'w', 'utf-8')
            f.write(str(value))
            f.close()

        cmd1 = str(command1.result)
        cmd2 = str(command2.result)
        # 默认错误
        notice = input_error()
        # 有两个指令时
        if command2.matched:
            # 计算数值
            if toolkits.is_number(cmd1) and toolkits.is_number(cmd2):
                target_value = int(cmd1) * int(cmd2)
                write_tar(target_value)
                notice = tar_set(target_value)
        # 有一个指令时
        elif command1.matched:
            # 随机难度
            if toolkits.check_string('d', cmd1):
                random_number = random.randint(1, 20)
                number_list = (re.findall(r'\d+', cmd1))
                level = int(''.join(number_list))
                target_value = int(level * random_number)
                write_tar(target_value)
                notice = tar_ran(random_number, target_value)
            # 单个数字
            elif toolkits.is_number(cmd1):
                target_value = int(cmd1)
                write_tar(target_value)
                notice = tar_set(target_value)
        # 没有其他指令, 直接发送数值
        elif not command2.matched and not command1.matched:
            target_value = g.get_tar()
            if target_value is None:
                notice = tar_none()
            else:
                notice = tar_is(target_value)
    await app.send_message(sender, MessageChain(notice))

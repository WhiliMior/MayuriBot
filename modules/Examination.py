import csv
import os
import random
import re

import pandas as pd
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
from graia.ariadne.util.saya import listen, dispatch

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.ex {属性/领域} 进行检定
上箭头表示该属性受到buff修饰
"""

buffed = '[↑]'


def no_chr(player):
    return f'{player}还没有角色×'


def no_tar():
    return f'没有目标数值×'


def no_attri(attribute):
    return f'没有找到属性[{attribute}]×'


def check_success():
    return f'🎉成功！'


def check_failure():
    return f'❗️失败！'


# 监听指令并回复
regular_expression = regex.Examination
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Examination(app: Ariadne, sender: Sender, target: Target,
                      command1: RegexResult):
    player_id = target.id
    group_id = sender.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name

    g = game_data.Group(group_id)
    target_value = g.get_tar()

    notice = 'error'
    error = True
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    elif target_value is None:
        notice = no_tar()
        error = True
    elif command1.matched:
        # 1个指令
        cmd1 = str(command1.result)
        buff_dataframe = p.buff_dataframe
        attribute_name = game_data.get_adv_cn_to_en(cmd1)
        if attribute_name is None:
            notice = no_attri(cmd1)
            error = True
        else:
            attribute_name_cn = game_data.advanced_en_to_cn[attribute_name]
            attribute_name_cn = attribute_name_cn.strip('检定_')
            # 没有buff就单纯拿出值
            if buff_dataframe is None:
                check_value = p.get_attribute_adv(cmd1)
                check_value_notice = check_value
            else:
                check_value, calculation_process = p.get_attribute_buffed(cmd1)
                check_value_notice = f'{buffed}{check_value}'
            success_rate = int(toolkits.reserve_zero_decimals(100 * check_value / (target_value * 5)))
            random_number = random.randint(1, 100)
            if random_number > success_rate:
                check_result = check_failure()
            else:
                check_result = check_success()
            if success_rate <= 0:
                ratio = 0
            else:
                ratio = toolkits.reserve_two_decimals(random_number / success_rate)
            # 只有正确处理才会变为没有error
            error = False

    if not error:
        notice = f'{str(character_name)}进行[{attribute_name_cn}]检定\n' \
               f'目标{str(target_value)} 比值{str(check_value_notice)}/{str(target_value * 5)}\n' \
               f'成功率：{str(success_rate)}%\n' \
               f'检定：{str(random_number)}/{str(success_rate)} ({ratio})\n' \
               f'{check_result}'

    await app.send_message(sender, MessageChain(notice))

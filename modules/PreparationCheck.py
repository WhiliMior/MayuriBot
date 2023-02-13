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
from graia.ariadne.util.saya import listen, dispatch

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.pre {属性} {影响数值} 计算时间
.pre {属性} {时间}t 计算数值
"""

buffed = '[↑]'


def no_chr(player):
    return f'{player}还没有角色×'


def no_attri(attribute):
    return f'没有找到属性[{attribute}]×'


def get_impact_number(p, attribute, number):
    buff_dataframe = p.buff_dataframe
    attribute_name = game_data.get_adv_cn_to_en(attribute)
    if attribute_name is None:
        return None
    attribute_name_cn = game_data.advanced_en_to_cn[attribute_name]
    attribute_name_cn = attribute_name_cn.strip('检定_')
    if buff_dataframe is None:
        attribute_value = p.get_attribute_adv(attribute)
        check_value_notice = attribute_value
    else:
        attribute_value, calculation_process = p.get_attribute_buffed(attribute)
        check_value_notice = f'{attribute_value} {buffed}'

    if toolkits.check_string('t', number):
        time = float(re.sub(r'[tT]', "", str(number)))
        impact_number = (attribute_value / 20) * time
    elif toolkits.is_number(number):
        impact_number = float(number)
        time = (impact_number * 20) / attribute_value

    time = toolkits.reserve_two_decimals(time)
    impact_number = toolkits.reserve_two_decimals(impact_number)

    return attribute_name_cn, check_value_notice, impact_number, time


def prep_check_result(p, attribute, number):
    character_name = p.character_name
    if not get_impact_number(p, attribute, number):
        return no_attri(attribute)
    attribute_name, check_value_notice, impact_number, time = get_impact_number(p, attribute, number)
    message = f'{character_name}: \n' \
              f'{attribute_name}: {check_value_notice}\n' \
              f'影响数值: {impact_number}\n' \
              f'时间: {time}'
    return message


# 监听指令并回复
regular_expression = regex.PreparationCheck
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def PreparationCheck(app: Ariadne, sender: Sender, target: Target,
                           command1: RegexResult, command2: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name

    notice = 'error'
    error = True
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    elif command2.matched:
        # 2个指令
        cmd1 = str(command1.result)
        cmd2 = str(command2.result)

        if toolkits.check_string(r'^[\u4e00-\u9fa5]+$', cmd1):
            attribute = cmd1
            number = cmd2
        else:
            attribute = cmd2
            number = cmd1

        notice = prep_check_result(p, attribute, number)

    await app.send_message(sender, MessageChain(notice))

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
.crd 体力/hp {变化值}
.crd 意志/mp {变化值}
.crd 现金/cash {变化值}
.crd reset
.crd
"""

buffed = '[↑]'


def no_chr(player):
    return f'{player}还没有角色×'


def cmd2_not_number():
    return f'请输入一个带正负号的数字作为第二个变量×'


def record_attri(character_name, attribute, attri_value_old, attri_value_new, attri_value_full):
    if attri_value_old > attri_value_new:
        change = '[↓]'
    elif attri_value_old < attri_value_new:
        change = '[↑]'
    else:
        change = '[=]'

    if attri_value_full == '':
        message = f'{character_name}: \n' \
                  f'[{attribute}]变更: {change}\n' \
                  f'{attri_value_old}→{attri_value_new}\n'
    else:
        ratio_old = int(toolkits.reserve_zero_decimals((attri_value_old / attri_value_full) * 100))
        ratio_new = int(toolkits.reserve_zero_decimals((attri_value_new / attri_value_full) * 100))
        message = f'{character_name}: \n' \
                  f'[{attribute}]变更: {change}\n' \
                  f'{attri_value_old}→{attri_value_new}/{attri_value_full}\n' \
                  f'{ratio_old}%→{ratio_new}%'
    return message


def reset_attri(character_name, hp, hp_full, mp, mp_full):
    message = f'{character_name}: \n' \
              f'状态重置\n' \
              f'体力: {hp}/{hp_full}\n' \
              f'意志: {mp}/{mp_full}'
    return message


def show_attri(character_name, hp, hp_full, mp, mp_full, cash):
    ratio_hp = int(toolkits.reserve_zero_decimals((hp / hp_full) * 100))
    ratio_mp = int(toolkits.reserve_zero_decimals((mp / mp_full) * 100))
    message = f'{character_name}: \n' \
              f'体力: {hp}/{hp_full} [{ratio_hp}%]\n' \
              f'意志: {mp}/{mp_full} [{ratio_mp}%]\n' \
              f'现金: {cash}'
    return message


# 监听指令并回复
regular_expression = regex.Record
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Record(app: Ariadne, sender: Sender, target: Target,
                 command1: RegexResult, command2: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character_crd = p.path_file_character_crd
    character_crd_dict = toolkits.json_to_dict(path_file_character_crd)

    notice = 'error'
    error = True
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    elif command2.matched:
        # 获取crd数据中的值
        hp = character_crd_dict['hp']
        mp = character_crd_dict['mp']
        cash = character_crd_dict['cash']
        hp_old = hp
        mp_old = mp
        cash_old = cash
        # 2个指令
        cmd1 = str(command1.result)
        cmd2 = str(command2.result)
        if not toolkits.is_number(cmd2):
            notice = cmd2_not_number
            error = True

        # 存储cmd1对应的变量名
        crd_mapper = {
            '体力|hp': ['hp', hp],
            '意志|mp': ['mp', mp],
            '现金|cash': ['cash', cash]
        }

        # 遍历crd_mapper字典，找到cmd1对应的变量
        for key, value in crd_mapper.items():
            if toolkits.check_string(cmd1, key):
                attri_value_old = value[1]
                if cmd2.startswith('+'):
                    value[1] += abs(float(cmd2[1:]))
                elif cmd2.startswith('-'):
                    value[1] -= abs(float(cmd2[1:]))
                attribute = value[0]
                attri_value_new = max(0, toolkits.reserve_one_decimals(value[1]))
                if attribute == 'cash':
                    attri_value_full = ''
                else:
                    attri_value_full = character_crd_dict[attribute + '_full']
                character_crd_dict[attribute] = attri_value_new
                break

        json_data = toolkits.dict_to_json(character_crd_dict)
        toolkits.write_file(path_file_character_crd, json_data)
        crd_en_to_cn = {'hp': '体力', 'mp': '意志', 'cash': '现金'}
        attribute_cn = crd_en_to_cn[attribute]
        notice = record_attri(character_name, attribute_cn, attri_value_old, attri_value_new, attri_value_full)
    elif command1.matched:
        cmd1 = str(command1.result)
        if toolkits.check_string('reset', cmd1):
            hp_full = character_crd_dict['hp_full']
            mp_full = character_crd_dict['mp_full']
            hp = hp_full
            mp = mp_full
            character_crd_dict['hp'] = hp
            character_crd_dict['mp'] = mp
            json_data = toolkits.dict_to_json(character_crd_dict)
            toolkits.write_file(path_file_character_crd, json_data)
            notice = reset_attri(character_name, hp, hp_full, mp, mp_full)
    elif not command2.matched and not command1.matched:
        hp_full = character_crd_dict['hp_full']
        mp_full = character_crd_dict['mp_full']
        hp = character_crd_dict['hp']
        mp = character_crd_dict['mp']
        cash = character_crd_dict['cash']
        notice = show_attri(character_name, hp, hp_full, mp, mp_full, cash)

    await app.send_message(sender, MessageChain(notice))

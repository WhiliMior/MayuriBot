import os
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
from modules import DamageReduction

"""
.crd 体力/hp {变化值}
.crd 意志/mp {变化值}
.crd 现金/cash {变化值}
.crd reset
.crd
"""


def no_chr(player):
    return f'{player}还没有角色×'


def cmd2_not_number():
    return f'数字错误×' \
           f'请输入一个带正负号的数字作为第二个变量'


def record_attri(character_name, attribute, attri_value_old, attri_value_new, attri_value_full, calculation_process):
    if attri_value_old > attri_value_new:
        change = '[↓]'
    elif attri_value_old < attri_value_new:
        change = '[↑]'
    else:
        change = '[=]'

    attri_value_change = toolkits.reserve_one_decimals(attri_value_new-attri_value_old)

    if calculation_process is None:
        calculation = ''
    else:
        calculation = f'\n{attri_value_change}={calculation_process}'

    if attri_value_full == '':
        message = f'{character_name}: \n' \
                  f'[{attribute}]变更: {change}{attri_value_change}{calculation}\n' \
                  f'{attri_value_old}→{attri_value_new}'
    else:
        difference = toolkits.reserve_one_decimals(attri_value_new - attri_value_full)
        ratio_old = int(toolkits.reserve_zero_decimals((attri_value_old / attri_value_full) * 100))
        ratio_new = int(toolkits.reserve_zero_decimals((attri_value_new / attri_value_full) * 100))
        message = f'{character_name}: \n' \
                  f'[{attribute}]变更: {change}{attri_value_change}{calculation}\n' \
                  f'{attri_value_old}→{attri_value_new}/{attri_value_full} ({difference})\n' \
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
              f'体力: {hp}/{hp_full} [{ratio_hp}%] ({hp-hp_full})\n' \
              f'意志: {mp}/{mp_full} [{ratio_mp}%] ({mp-mp_full})\n' \
              f'现金: {cash}'
    return message


# 监听指令并回复
regular_expression = regex.Record
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command3" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Record(app: Ariadne, sender: Sender, target: Target,
                 command1: RegexResult, command2: RegexResult, command3: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character_crd = p.path_file_character_crd
    path_reduction_character = p.path_reduction_character
    try:
        character_crd_dict = toolkits.json_to_dict(path_file_character_crd)
    except FileNotFoundError:
        pass

    notice = 'error'
    error = False
    calculation_process = None
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
        # 查询是否有第三个伤害类型的输入
        if command3.matched:
            cmd3 = str(command3.result)
            source_type = cmd3
        # 没有输入则为无类型
        else:
            source_type = None
        if not toolkits.is_number(cmd2):
            if not cmd2.startswith('+') and not cmd2.startswith('-'):
                notice = cmd2_not_number()
                error = True
        if not error:
            # 存储cmd1对应的变量名
            crd_mapper = {
                '体力|hp': ['hp', hp],
                '意志|mp': ['mp', mp],
                '现金|cash': ['cash', cash]
            }

            # 遍历crd_mapper字典，找到cmd1对应的变量
            for key, value in crd_mapper.items():
                if toolkits.check_string(cmd1, key):
                    # value[1]指的是具体的体力值等
                    attri_value_old = value[1]
                    attribute = value[0]
                    if cmd2.startswith('+'):
                        source_range = f'+{attribute}'
                    elif cmd2.startswith('-'):
                        source_range = f'-{attribute}'

                    if os.path.exists(path_reduction_character):
                        # cmd2[1:] 指的是具体的伤害数字
                        result = p.get_damage_reduced(float(cmd2), source_range, source_type)
                        attri_value_new = attri_value_old + result[0]
                        calculation_process = result[1]
                    else:
                        attri_value_new = attri_value_old + float(cmd2)

                    # 计算新的数据
                    attri_value_new = max(0, toolkits.reserve_one_decimals(attri_value_new))
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
            notice = record_attri(character_name, attribute_cn, attri_value_old, attri_value_new, attri_value_full, calculation_process)
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

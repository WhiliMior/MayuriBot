import csv
import json
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
from graia.ariadne.model import Group, Friend
from graia.ariadne.util.saya import listen, dispatch

from modules import WeaponCreate
from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.bat #直接显示时间轴
.bat end #删除时间轴
.bat out #退出战斗
.bat {属性} {时间}t/{影响数值} (笔记) #战斗指令
.bat wp {时间}t/{影响数值} (笔记) #武器指令
    增幅武器可以使用t或者数字
    火力武器只可以使用数字
    其他武器不可以使用指令
"""


def no_chr(player):
    return f'{player}还没有角色×'


def type_friend():
    return '战斗指令仅在群聊使用×'


def no_attri(attribute):
    return f'没有找到属性[{attribute}]×'


def wp_reload(current_load, full_load):
    return f'武器已经装填√\n' \
           f'当前弹药: {current_load}/{full_load}'


def wp_load_full(current_load, full_load):
    return f'武器弹药已满×\n' \
           f'当前弹药: {current_load}/{full_load}'


def not_enough_load(current_load, full_load):
    return f'没有足够的弹药×\n' \
           f'当前弹药: {current_load}/{full_load}'

def no_support_other_weapon_type():
    return f'战斗指令不支持[其他]类型武器×'
def no_battle_data():
    return f'没有战斗数据×'


def no_battle_character(character):
    return f'角色[{character}]没有参与战斗×'


def quit_battle(character):
    return f'角色[{character}]退出战斗√'


def end_battle():
    return f'战斗结束，时间轴归位√'


def wp_artillery_wrong_input():
    return f'武器指令错误×\n' \
           f'火力武器必须使用数字作为发射弹药数！'


# 把dataframe中的数据打成轴
def print_battle_dataframe(battle_dataframe):
    battle_dataframe = battle_dataframe.fillna('')

    result = ''
    for index, row in battle_dataframe.iterrows():
        player_id = row['玩家']
        character = row['角色']
        attribute = row['相关属性']
        time = row['行动时间']
        impact_number = row['影响数值']
        note = row['笔记']
        using_weapon = row['使用武器']
        weapon_id = row['武器序号']
        cumulative_time = row['累计行动时间']
        cumulative_impact_number = row['累计影响数值']

        if using_weapon:
            p = game_data.Player(player_id, character)
            weapon_dataframe = p.weapon_dataframe
            weapon_dataframe = weapon_dataframe.fillna('')
            weapon_id = int(weapon_id)
            weapon_list = weapon_dataframe.iloc[weapon_id].fillna('').tolist()
            wp_name = weapon_list[0]
            wp_type = weapon_list[1]
            wp_attribute = weapon_list[2]
            wp_damage = weapon_list[3]
            wp_range = weapon_list[5]
            wp_note = weapon_list[10]

            # 换为中文
            type_list_en_to_cn = WeaponCreate.type_list_en_to_cn
            if wp_type in type_list_en_to_cn:
                weapon_list[1] = type_list_en_to_cn[wp_type]
            # 十一个属性
            a = game_data.AttributesList
            basic_en_to_cn = a.basic_en_to_cn
            if wp_attribute in basic_en_to_cn:
                attribute_name = weapon_list[2] = basic_en_to_cn[wp_attribute]

            # 看看用户有没有输入note
            if note == '':
                line_note = ''
            else:
                line_note = f'\n{note}'

            # 看看武器有没有备注
            if wp_note == '':
                line_wp_note = ''
            else:
                line_wp_note = f'（{wp_note}）'

            # 三种武器的输出
            if wp_type == 'amplifier':
                line_explanations = f'{wp_name} : {attribute_name}{line_wp_note}' \
                                    f'{line_note}'
            elif wp_type == 'artillery':
                max_load = weapon_list[6]
                current_load = weapon_list[7]
                if impact_number == 0:
                    impact_number = '整备中...'
                line_explanations = f'{wp_name}{line_wp_note}\n' \
                                    f'[{current_load}/{max_load}]' \
                                    f'{line_note}'
            else:
                line_explanations = ''
        # 不使用武器
        else:
            # 看看用户有没有输入note
            if note == '':
                line_note = ''
            else:
                line_note = f' : {note}'
            line_explanations = f'{attribute}{line_note}'

        action_print = f'{character} : {cumulative_impact_number}\n' \
                       f'{cumulative_time}t ({time}t) : {impact_number}\n' \
                       f'{line_explanations}\n' \
                       f'———————\n'
        result += action_print

    return result


# 监听指令并回复
regular_expression = regex.Battle
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command3" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Battle(app: Ariadne, sender: Sender, target: Target,
                 command1: RegexResult, command2: RegexResult, command3: RegexResult):
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
    # 判断消息来源:群聊or私聊? 提取群聊发送者qq
    elif isinstance(sender, Friend):
        notice = type_friend()
        error = True
    elif isinstance(sender, Group):
        g = game_data.Group(sender.id)
        path_group_folder = g.path_group_folder
        path_group_file_bat = g.path_group_file_bat
        error = False

    if command2.matched and not error:
        # 2个指令
        cmd1 = str(command1.result)
        cmd2 = str(command2.result)
        if command3.matched:
            cmd3 = str(command3.result)
            note = cmd3
        else:
            note = ''

        use_weapon = False
        if toolkits.check_string('wp', cmd1):
            use_weapon = True
            if toolkits.is_number(cmd2):
                number = float(cmd2)
            else:
                number = str(cmd2)

            weapon_dataframe = p.weapon_dataframe
            path_weapon_character = p.path_weapon_character
            using_index = int(weapon_dataframe["using"].idxmax())
            weapon_list = weapon_dataframe.iloc[using_index].fillna('').tolist()
            wp_name = weapon_list[0]
            wp_type = weapon_list[1]
            wp_attribute = weapon_list[2]
            wp_damage = weapon_list[3]

            wp_range = weapon_list[5]

            wp_note = weapon_list[10]

            # 换为中文
            type_list_en_to_cn = WeaponCreate.type_list_en_to_cn
            if wp_type in type_list_en_to_cn:
                weapon_list[1] = type_list_en_to_cn[wp_type]
            # 十一个属性
            a = game_data.AttributesList
            basic_en_to_cn = a.basic_en_to_cn
            if wp_attribute in basic_en_to_cn:
                attribute_name = weapon_list[2] = basic_en_to_cn[wp_attribute]

            if wp_type == 'amplifier':
                number = str(number)
                attribute_name, check_value_notice, impact_number, time = p.get_impact_number(attribute_name, number)
                impact_number = impact_number * (1 + (wp_damage / 100))
                impact_number = toolkits.reserve_one_decimals(impact_number)
            elif wp_type == 'artillery':
                attribute_name = ''
                wp_maxload = weapon_list[6]
                current_load = weapon_list[7]
                if toolkits.check_string('re[load]?', cmd2):
                    if current_load == wp_maxload:
                        notice = wp_load_full(current_load, wp_maxload)
                        error = True
                    else:
                        # reload
                        reload_time = weapon_list[8]
                        time = reload_time
                        impact_number = 0

                        weapon_dataframe.loc[using_index, 'current_load'] = wp_maxload
                        current_load = weapon_dataframe.loc[using_index, 'current_load']
                        weapon_dataframe.to_csv(path_weapon_character, index=False)
                        notice = wp_reload(current_load, wp_maxload)
                else:
                    if not toolkits.is_number(number):
                        error = True
                        notice = wp_artillery_wrong_input()
                    else:
                        number = int(toolkits.reserve_zero_decimals(number))
                        cast = weapon_list[4]
                        load = weapon_list[6]

                        if number > current_load:
                            notice = not_enough_load(current_load, load)
                            error = True
                        else:
                            current_load -= number
                            damage = wp_damage * number
                            damage = toolkits.reserve_two_decimals(damage)
                            impact_number = damage
                            time = cast * number

                            weapon_dataframe.loc[using_index, 'current_load'] = current_load
                            weapon_dataframe.to_csv(path_weapon_character, index=False)
            elif wp_type == 'other':
                notice = no_support_other_weapon_type()
                error = True
        elif toolkits.check_string(r'^[\u4e00-\u9fa5]+$', cmd1):
            attribute = cmd1
            number = cmd2
        else:
            attribute = cmd2
            number = cmd1

        if not error:
            if use_weapon:
                p.get_character()
                weapon_dataframe = p.weapon_dataframe
                using_index = int(weapon_dataframe["using"].idxmax())
            else:
                using_index = ''
                attribute_name, check_value_notice, impact_number, time = p.get_impact_number(attribute, number)

            cumulative_time = time
            cumulative_impact_number = impact_number
            header = ['玩家', '角色', '相关属性', '行动时间', '影响数值',
                      '笔记', '使用武器', '武器序号', '累计行动时间', '累计影响数值']
            time = toolkits.reserve_two_decimals(time)
            impact_number = toolkits.reserve_one_decimals(impact_number)
            battle_list = [player_id, character_name, attribute_name, time, impact_number,
                           note, use_weapon, using_index, cumulative_time, cumulative_impact_number]

            # 写入dataframe
            # 写入时检测是否已有角色
            if os.path.exists(path_group_file_bat):
                csv_file = open(path_group_file_bat, 'r', newline='', encoding='utf-8-sig', errors='ignore')
                battle_dataframe = pd.read_csv(csv_file, header=0, sep=',')
                csv_file.close()
                # 存在角色
                if not battle_dataframe[(battle_dataframe['玩家'] == player_id) &
                                        (battle_dataframe['角色'] == character_name)].empty:
                    # 存在符合条件的行
                    row_index = battle_dataframe[(battle_dataframe['玩家'] == player_id) & (
                            battle_dataframe['角色'] == character_name)].index[0]
                    # 读取累计数值
                    cumulative_time = battle_dataframe.at[row_index, '累计行动时间']
                    cumulative_impact_number = battle_dataframe.at[row_index, '累计影响数值']
                    cumulative_time += time
                    cumulative_impact_number += impact_number
                    battle_list[-2] = toolkits.reserve_two_decimals(cumulative_time)
                    battle_list[-1] = toolkits.reserve_one_decimals(cumulative_impact_number)

                    battle_dataframe.iloc[row_index, :] = battle_list

                else:
                    # 不存在符合条件的行
                    # 最后一行加上新行动
                    battle_dataframe.loc[-1] = battle_list
                # 排序
                battle_dataframe = battle_dataframe.sort_values(by=['累计行动时间'],
                                                                ascending=[True])
                battle_dataframe.to_csv(path_group_file_bat, index=False)
            # 没有
            else:
                # 写入文件
                toolkits.check_folder(path_group_folder)
                csv_file = open(path_group_file_bat, 'w', newline='', encoding='utf-8-sig', errors='ignore')
                writer = csv.writer(csv_file)
                writer.writerow(header)
                writer.writerow(battle_list)
                csv_file.close()

            csv_file = open(path_group_file_bat, 'r', newline='', encoding='utf-8-sig', errors='ignore')
            battle_dataframe = pd.read_csv(csv_file, header=0, sep=',')
            csv_file.close()
            notice = print_battle_dataframe(battle_dataframe)
    elif command1.matched and not error:
        cmd1 = str(command1.result)

        if not os.path.exists(path_group_file_bat):
            notice = no_battle_data()
            error = True
        # 删除时间轴
        elif toolkits.check_string('end', cmd1) and not error:
            os.remove(path_group_file_bat)
            notice = end_battle()
            error = True
        # 没有找到角色
        else:
            csv_file = open(path_group_file_bat, 'r', newline='', encoding='utf-8-sig', errors='ignore')
            battle_dataframe = pd.read_csv(csv_file, header=0, sep=',')
            csv_file.close()
            if battle_dataframe[(battle_dataframe['玩家'] == player_id) &
                                (battle_dataframe['角色'] == character_name)].empty:
                notice = no_battle_character(character_name)
                error = True

        # 退出战斗
        if toolkits.check_string('out', cmd1) and not error:
            # 存在符合条件的行
            csv_file = open(path_group_file_bat, 'r', newline='', encoding='utf-8-sig', errors='ignore')
            battle_dataframe = pd.read_csv(csv_file, header=0, sep=',')
            csv_file.close()
            row_index = battle_dataframe[(battle_dataframe['玩家'] == player_id) &
                                         (battle_dataframe['角色'] == character_name)].index[0]
            # 删除该行
            battle_dataframe = battle_dataframe.drop(row_index, axis=0)
            battle_dataframe.to_csv(path_group_file_bat, index=False)
            notice = quit_battle(character_name)
    elif not command1.matched and not error:
        csv_file = open(path_group_file_bat, 'r', newline='', encoding='utf-8-sig', errors='ignore')
        battle_dataframe = pd.read_csv(csv_file, header=0, sep=',')
        csv_file.close()

        notice = print_battle_dataframe(battle_dataframe)

    await app.send_message(sender, MessageChain(notice))

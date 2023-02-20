import csv
import os
import re

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import (
    RegexResult,
    RegexMatch,
    Twilight,
    SpacePolicy,
    WildcardMatch,
)
from graia.ariadne.util.saya import listen, dispatch

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.WPsetup '名称', '类型', '增幅属性', '伤害', '前摇', '射程', '载弹量', '当前载弹', '装填时间', '负重', '备注', '使用'
"""

# 所有要记录的条目
header_en = ['name', 'type', 'attribute', 'damage', 'cast', 'range', 'load', 'current_load', 'reload_time', 'weight',
             'note', 'using']
header_cn = ['名称', '类型', '增幅属性', '伤害', '前摇', '射程', '载弹量', '当前载弹', '装填时间', '负重', '备注',
             '使用']
header_cn_to_en = game_data.combine_lists_to_dict(header_cn, header_en)
header_en_to_cn = game_data.combine_lists_to_dict(header_en, header_cn)
# 3种type
type_list_en = ['amplifier', 'artillery', 'other']
type_list_cn = ['增幅', '火力', '其他']
type_list_cn_to_en = game_data.combine_lists_to_dict(type_list_cn, type_list_en)
type_list_en_to_cn = game_data.combine_lists_to_dict(type_list_en, type_list_cn)
# 十一个属性
a = game_data.AttributesList
basic_eleven_cn = a.basic_eleven_cn
basic_cn_to_en = a.basic_cn_to_en


def no_chr(player):
    return f'{player}还没有角色×'


def wrong_command():
    return f'指令错误!'


def wrong_attribute(attribute):
    return f'不可使用属性[{attribute}]×'


def wrong_type(type):
    return f'不存在武器类型[{type}]×'


def weapon_create(character_name, weapon_name):
    return f'{character_name}增加武器[{weapon_name}]√'


# 监听指令并回复
regular_expression = regex.WeaponCreate
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ WildcardMatch()
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def WeaponCreate(app: Ariadne, sender: Sender, target: Target,
                       command1: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_weapon_character = p.path_weapon_character

    notice = 'error'
    error = False
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    else:
        cmd1 = str(command1.result)
        # 字段分隔
        end_divider = ','
        middle_divider = ':'

        full_text = cmd1
        # 将文本变成list
        attribute_list = full_text.split(end_divider)

        # 创建一个字典，然后将属性写入其中
        weapon_property = {}
        for element in attribute_list:
            two_values = element.split(middle_divider)
            attribute = two_values[0]
            if attribute in header_cn_to_en:
                attribute = header_cn_to_en[attribute]
            else:
                notice = wrong_command()
                error = True
                break
            value = two_values[1]
            # 属性为空则用0替代
            if len(value) == 0:
                value = ''
            if toolkits.is_number(value):
                value = float(value)
            weapon_property[attribute] = value
        if not error:
            wp_name = weapon_property['name']
            wp_type = weapon_property['type']
            wp_attribute = weapon_property['attribute']
            wp_damage = weapon_property['damage']
            wp_cast = weapon_property['cast']
            wp_range = weapon_property['range']
            wp_load = weapon_property['load']
            if wp_load == '':
                wp_load_current = ''
            else:
                wp_load_current = 0
            # type换成英文
            if wp_type in type_list_cn_to_en:
                wp_type = type_list_cn_to_en[wp_type]
                # amplifier
                if wp_type == type_list_en[0]:
                    wp_load_current = ''
                    # 检测attribute
                    if wp_attribute in basic_eleven_cn:
                        wp_attribute = basic_cn_to_en[wp_attribute]
                    else:
                        notice = wrong_attribute(wp_attribute)
                        error = True
                # artillery
                elif wp_type == type_list_en[1]:
                    wp_load = int(wp_load)
                    wp_load_current = wp_load
                    wp_attribute = ''
            # 留空
            elif wp_type == '':
                wp_type = type_list_en[2]
            else:
                notice = wrong_type(wp_type)
                error = True

            wp_reload_time = weapon_property['reload_time']
            wp_weight = weapon_property['weight']
            wp_note = weapon_property['note']
            wp_using = 1
            weapon_list = [wp_name,
                           wp_type,
                           wp_attribute,
                           wp_damage,
                           wp_cast,
                           wp_range,
                           wp_load,
                           wp_load_current,
                           wp_reload_time,
                           wp_weight,
                           wp_note,
                           wp_using]

        if not error:
            if os.path.exists(path_weapon_character):
                weapon_dataframe = p.weapon_dataframe
                # 检测是否已有角色
                weapon_dataframe['using'] = weapon_dataframe['using'].replace(1, 0)
                weapon_dataframe.loc[-1] = weapon_list
                # 排序
                weapon_dataframe = weapon_dataframe.sort_values(by=header_en)
                weapon_dataframe.to_csv(path_weapon_character, index=False)
            else:
                csv_file = open(path_weapon_character, 'w', newline='', encoding='utf-8-sig', errors='ignore')
                writer = csv.writer(csv_file)
                writer.writerow(header_en)
                writer.writerow(weapon_list)
                csv_file.close()
                weapon_dataframe = p.weapon_dataframe

            path_file_character = p.path_file_character
            path_file_character_adv = p.path_file_character_adv
            # 添加负重到角色
            attri_dict = toolkits.json_to_dict(path_file_character)
            current_weight = attri_dict['weight']
            # 求和weapon weight
            weapon_weight = wp_weight
            # 添加到人物
            character_weight = current_weight + weapon_weight
            # 重新计算高级属性
            result_notice = p.change_weight(wp_weight)

            notice = weapon_create(character_name, wp_name) + '\n' + result_notice

    await app.send_message(sender, MessageChain(notice))

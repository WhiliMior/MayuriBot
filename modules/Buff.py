import csv
import os
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
.buff {来源} {属性} {数值} {类型}
.buff del {序号}
.buff {属性或范围}
.buff
"""

# 所有要记录的条目
header = ['source', 'range', 'value', 'type']
# 所有的range
r_physical = ['check_constitution', 'check_dexterity', 'check_strength']
r_field = ['check_medicine_and_life_science', 'check_engineering_and_technology',
           'check_military_and_survival', 'check_literature', 'check_visual_and_performing_art']
r_mental = ['check_willpower', 'check_education', 'check_intelligence'] + r_field
r_all = r_physical + r_mental
r_cn_to_en = {'物理': 'r_physical', '领域': 'r_field', '思维': 'r_mental', '所有': 'r_all'}
r_en_to_list = {'r_physical': r_physical, 'r_field': r_field, 'r_mental': r_mental, 'r_all': r_all}
r_en_to_cn = {v: k for k, v in r_cn_to_en.items()}
# 四种type
type_list_en = ['direct_add', 'direct_time', 'final_add', 'final_time']
type_list_cn = ['直接加算', '直接乘算', '最终加算', '最终乘算']
type_list_cn_to_en = game_data.combine_lists_to_dict(type_list_cn, type_list_en)
type_list_en_to_cn = game_data.combine_lists_to_dict(type_list_en, type_list_cn)


def no_chr(player):
    return f'{player}还没有角色×'


def no_buff(character_name):
    return f'{character_name}还没有buff×'


def add_buff(character_name, buff_name):
    return f'{character_name}增加buff[{buff_name}]√'


def wrong_range(range_input):
    return f'属性错误×\n' \
           f'不存在属性[{range_input}]'


def wrong_value():
    return f'数值错误×\n' \
           f'应为数字或百分数'


def wrong_type():
    return f'类型错误×\n' \
           f'类型应为数字1-4或汉字类型名称'


def wrong_index():
    return f'序号错误×'


def del_buff(index):
    return f'删除buff {index}√'


# 监听指令并回复
regular_expression = regex.Buff
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command3" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command4" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Buff(app: Ariadne, sender: Sender, target: Target,
               command1: RegexResult, command2: RegexResult, command3: RegexResult, command4: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name

    a = game_data.AttributesList
    basic_cn = a.basic_cn
    basic_en_to_cn = a.basic_en_to_cn
    advanced_en = a.advanced_en
    advanced_cn_to_en = a.advanced_cn_to_en
    advanced_en_to_cn = a.advanced_en_to_cn

    buff_dataframe = p.buff_dataframe

    notice = 'error'
    error = False
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    else:
        # 四个指令
        buff_source = str(command1.result)
        buff_range = str(command2.result)
        buff_value = str(command3.result)
        buff_value_input = str(command3.result)
        buff_type = str(command4.result)

        path_buff_character = p.path_buff_character
        buff_dataframe = p.buff_dataframe

        # 有3个指令时
        if command3.matched:
            # 处理range, 看看是否输入了一个大range
            if buff_range in r_cn_to_en:
                # 如果是, 那么把这个range 的英文提取出来
                buff_range = r_cn_to_en[buff_range]
            else:
                # 换成英文
                buff_range = game_data.get_adv_cn_to_en(buff_range)
                if not buff_range in advanced_en:
                    notice = wrong_range(buff_range)
                    error = True

            # 处理value, 判断是否含有%
            if toolkits.check_string('%', buff_value_input):
                # 去掉%
                buff_value = float(buff_value.strip('%'))
                if toolkits.is_number(buff_value):
                    buff_value = buff_value / 100.0
                else:
                    notice = wrong_value()
                    error = True
            # 判断是否为数字
            elif not toolkits.is_number(buff_value):
                notice = wrong_value()
                error = True
            # 判断有无第四个指令
            if command4.matched:
                # 处理type
                if buff_type in type_list_cn_to_en:
                    # 换成英文
                    buff_type = type_list_cn_to_en[buff_type]
                elif toolkits.is_number(buff_type):
                    index = int(buff_type) - 1
                    if 0 <= index <= 3:
                        buff_type = type_list_en[index]
                    else:
                        notice = wrong_type()
                        error = True
                else:
                    notice = wrong_type()
                    error = True
            # 没有第四指令
            else:
                if toolkits.check_string('%', buff_value_input):
                    # 同时定义type
                    buff_type = 'direct_time'
                elif toolkits.is_number(buff_value):
                    # 同时定义type
                    buff_type = 'direct_add'

            # 没有错误就正常操作
            if not error:
                # 增加buff
                buff_list = [buff_source, buff_range, buff_value, buff_type]

                # 写入dataframe
                # 写入时检测是否已有buff
                if os.path.exists(path_buff_character):
                    # 最后一行加上新buff
                    buff_dataframe.loc[-1] = buff_list
                    # 排序
                    buff_dataframe = buff_dataframe.sort_values(by=['range', 'type', 'value', 'source'], ascending=[False, False, True, True])
                    buff_dataframe.to_csv(path_buff_character, index=False)
                # 没有
                else:
                    # 写入文件
                    csv_file = open(path_buff_character, 'w', newline='', encoding='utf-8-sig', errors='ignore')
                    writer = csv.writer(csv_file)
                    writer.writerow(header)
                    writer.writerow(buff_list)
                notice = add_buff(character_name, buff_source)
        # 两个指令
        elif command2.matched:
            # 删除buff
            cmd1 = str(command1.result)
            cmd2 = str(command2.result)
            if toolkits.check_string('del', cmd1):
                if buff_dataframe is None:
                    notice = no_buff(character_name)
                    error = True
                elif toolkits.check_string('all', cmd2):
                    os.remove(path_buff_character)
                else:
                    index = str(command2.result)
                    notice = del_buff(index)
                    if toolkits.is_number(index):
                        index = int(index) - 1
                        # 序号超过范围
                        if 0 > index or index > len(buff_dataframe):
                            notice = wrong_index()
                            error = True
                    else:
                        notice = wrong_index()
                        error = True

                if not error:
                    if len(buff_dataframe) <= 1:
                        os.remove(path_buff_character)
                    else:
                        buff_dataframe = buff_dataframe.drop(index)
                        buff_dataframe.to_csv(path_buff_character, index=False)
        # 一个指令或没有指令, 打印buff列表
        elif not command2.matched:
            # 无buff错误输出
            if buff_dataframe is None:
                notice = no_buff(character_name)
                error = True
            else:
                attri_name = None
                count = 0
                send_list = []
                content = f'{character_name}共有{len(buff_dataframe)}个属性修饰'
                # 如果有属性输入
                if command1.matched:
                    cmd1 = str(command1.result)
                    # 如果输入的是一个大类
                    if cmd1 in r_cn_to_en:
                        attri_name_cn = cmd1
                        attri_name = r_cn_to_en[attri_name_cn]
                        attri_name = r_en_to_list[attri_name]
                    else:
                        attri_name = game_data.get_adv_cn_to_en(cmd1)
                        if attri_name is None:
                            notice = wrong_range(cmd1)
                            error = True
                        else:
                            attri_name_cn = advanced_en_to_cn[attri_name]
                            attri_name_cn = attri_name_cn.strip('检定_')
                if not error:
                    for index, data in buff_dataframe.iterrows():

                        buff_index = f'[{index + 1}]'
                        buff_source = f"{data['source']}"
                        buff_range = data['range']

                        # 计算总共受到影响的属性
                        buff_range_list = []
                        if buff_range in r_en_to_list:
                            buff_range_list = r_en_to_list[buff_range]
                        elif buff_range in advanced_en:
                            buff_range_list = [buff_range]
                        # 没有属性就跳出循环
                        if attri_name is not None:
                            # 属性不在range中
                            if attri_name not in buff_range_list:
                                # list不在range中
                                if not set(attri_name) <= set(buff_range_list):
                                    continue

                        count += 1

                        # buff range 换为中文
                        if buff_range in r_en_to_cn:
                            buff_range = r_en_to_cn[buff_range]
                        elif buff_range in advanced_en:
                            buff_range = advanced_en_to_cn[buff_range]
                            buff_range = buff_range.strip('检定_')

                        buff_value = data['value']

                        buff_type = data['type']
                        if buff_type in ['direct_time', 'final_time']:
                            buff_value = format(float(buff_value) * 100, '.0f') + '%'
                        buff_type = type_list_en_to_cn[buff_type]

                        # 最终美化
                        insert = chr(12288)
                        dash = '—'
                        buff_source = f"📍{buff_source}"
                        buff_range = f"🏷{buff_range}"
                        buff_type = f"{buff_type}"
                        buff_value = f"{buff_value}"

                        send_list.append(
                            f"{buff_index:<}"
                            f"{buff_source:{insert}<8}|"
                            f"{buff_value:^8}"
                            f"\n"
                            f"---"
                            f"{buff_range:{dash}<8}"
                            f"{buff_type:{insert}>4}")

                    if command1.matched and count == 0:
                        content = f'{character_name}的[{attri_name_cn}]没有属性修饰'
                    elif command1.matched:
                        content = f'{character_name}的[{attri_name_cn}]共有{count}个属性修饰'
                    content = content + '\n' + "\n".join(send_list)
                    # 属性下没有buff

                    notice = content


    await app.send_message(sender, MessageChain(notice))

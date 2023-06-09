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
+hp/mp：带+号意味着对增加该资源有改变。例如增加治疗量，减少治疗量
-hp/mp：带-号意味着对减少该资源有改变，例如增加受伤量，减少受伤量

+指令最后的结果没有上下限：即可能出现总数超过100%的减疗，此时治疗效果会变为伤害
-指令最大结果为：使用-指令减少资源时，影响为0.

数值有三种：数字带%，纯数字，数字带c（convert）
带%是百分比减，不带%是固定减。c意味着将影响数值转换为百分比减

伤害类型指的是该减伤对哪种伤害来源有效果，例如物理，魔法，真实伤害。

4指令：
.dr {来源} {+/-}{hp/mp/all} {数值} {伤害类型}
不加正负号默认为-，也就是减伤或增伤
如果是减伤，那么单个百分比减不能超过100%
如果是减疗，那么单个百分比减不能少于-100%
伤害类型为bypass或bp时，会无视一切已记录的减伤
3指令：
.dr {来源} {+/-}{hp/mp/all} {数值}
.dr del {序号}
.dr del all
2指令：
.dr {+/-}{hp/mp/all}
1指令：
.dr
"""

# 所有要记录的条目
header = ['source', 'range', 'value', 'type', 'defence']
# 所有的range
r_sign = ['+', '-']
r_hp = ['hp', '体力']
r_mp = ['mp', '意志']
r_all = ['all', '所有']
r_every = ['+hp', '-hp', '+mp', '-mp', '+all', '-all']
r_en_to_cn = {'+hp': '+体力', '-hp': '-体力', '+mp': '+意志', '-mp': '-意志', '+all': '+所有', '-all': '-所有'}


# 处理range, 看看输入了哪个range
def normalize_range(range_input):
    range_input = range_input.strip().lower()

    if range_input.startswith('+') or range_input.startswith('-'):
        # 去除正负号，并将关键词替换为缩写
        sign = range_input[0]
        range_input = range_input[1:].replace('体力', 'hp').replace('意志', 'mp').replace('所有', 'all')
        return sign + range_input
    else:
        # 将关键词替换为缩写
        range_input = range_input.replace('体力', 'hp').replace('意志', 'mp').replace('所有', 'all')
        if range_input in ['hp', 'mp', 'all']:
            return '-' + range_input  # 返回已转换的范围类型

    return False  # 返回错误标识


def calculate_reduction(value, level, type):
    reduction = 0
    if type == '-':
        reduction = value / (value + (level * 10))
    elif type == '+':
        reduction = value / (level * 10)
    reduction = toolkits.reserve_two_decimals(reduction)
    return reduction


def no_chr(player):
    return f'{player}还没有角色×'


def no_buff(character_name):
    return f'{character_name}没有资源变化修饰×'


def add_reduction(character_name, reduction_list):
    if reduction_list[4] == 1:
        defence = '🛡'
    else:
        defence = '📍'
    return f'{character_name}增加资源变化修饰 [{reduction_list[0]}]√\n' \
           f'{defence}{reduction_list[1]} [{reduction_list[2]}] {reduction_list[3]}'


def wrong_range(range_input):
    return f'范围错误×\n' \
           f'不存在范围 [{range_input}]\n' \
           f'范围可选：(+/-)(hp/mp/all)'


def wrong_value():
    return f'数值错误×\n' \
           f'应为数字或百分数'


def wrong_index():
    return f'序号错误×'


def del_buff(index):
    return f'删除资源变化修饰 [{index}]√'


def del_buff_all():
    return f'删除所有资源变化修饰√'


# 监听指令并回复
regular_expression = regex.DamageReduction
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command3" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command4" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def DamageReduction(app: Ariadne, sender: Sender, target: Target,
                          command1: RegexResult, command2: RegexResult, command3: RegexResult, command4: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character = p.path_file_character

    notice = 'error'
    error = False
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    else:
        # 四个指令
        reduction_source = str(command1.result)
        reduction_range = str(command2.result)
        reduction_value = str(command3.result)
        reduction_value_input = str(command3.result)
        reduction_type = str(command4.result)

        path_reduction_character = p.path_reduction_character
        reduction_dataframe = p.reduction_dataframe

        # 有3个指令时
        if command3.matched:

            if normalize_range(reduction_range) is False:
                notice = wrong_range(reduction_range)
                error = True
            else:
                reduction_range = normalize_range(reduction_range)

            defence = 0
            # 处理value, 判断是否含有%
            if toolkits.check_string('%', reduction_value_input):
                # 去掉%
                reduction_value = float(reduction_value.strip('%'))
                if toolkits.is_number(reduction_value):
                    reduction_value = reduction_value / 100.0
                    reduction_value = toolkits.reserve_two_decimals(reduction_value)
                    # 转换百分数
                    reduction_value = '{:.0%}'.format(reduction_value)
                else:
                    notice = wrong_value()
                    error = True
            # 如果不含%，则判断是否含c
            elif toolkits.check_string('d', reduction_value_input):
                # 去掉c
                reduction_value = float(reduction_value.strip('d'))
                if toolkits.is_number(reduction_value):
                    # attri_dict_basic = toolkits.json_to_dict(path_file_character)
                    # level = attri_dict_basic['level']
                    defence = 1
                    reduction_value = reduction_value
                else:
                    notice = wrong_value()
                    error = True
            # 如果均不含，则判断是否为纯数字
            elif toolkits.is_number(reduction_value):
                reduction_value = toolkits.reserve_two_decimals(float(reduction_value))
            elif not toolkits.is_number(reduction_value):
                notice = wrong_value()
                error = True

            # 判断有无第四个指令
            if command4.matched:
                # 处理type
                reduction_type = reduction_type
            # 没有第四指令，则type为默认，也就是所有类型
            else:
                reduction_type = '所有'

            # 数据录入没有错误就开始正常操作
            if not error:
                # 增加buff
                reduction_list = [reduction_source, reduction_range, reduction_value, reduction_type, defence]

                # 写入dataframe
                # 写入时检测是否已有buff
                if os.path.exists(path_reduction_character):
                    # 最后一行加上新buff
                    reduction_dataframe.loc[-1] = reduction_list
                    # 排序
                    reduction_dataframe = reduction_dataframe.sort_values(by=['defence', 'range', 'type', 'value', 'source'],
                                                                          ascending=[False, False, False, True, True])
                    reduction_dataframe.to_csv(path_reduction_character, index=False)
                # 没有
                else:
                    # 写入文件
                    csv_file = open(path_reduction_character, 'w', newline='', encoding='utf-8-sig', errors='ignore')
                    writer = csv.writer(csv_file)
                    writer.writerow(header)
                    writer.writerow(reduction_list)
                notice = add_reduction(character_name, reduction_list)
        # 两个指令
        elif command2.matched:
            # 删除buff
            cmd1 = str(command1.result)
            cmd2 = str(command2.result)
            if toolkits.check_string('del', cmd1):
                if reduction_dataframe is None:
                    notice = no_buff(character_name)
                    error = True
                elif toolkits.check_string('all', cmd2):
                    os.remove(path_reduction_character)
                    notice = del_buff_all()
                    error = True
                else:
                    index = str(command2.result)
                    notice = del_buff(index)
                    if toolkits.is_number(index):
                        index = int(index) - 1
                        # 序号超过范围
                        if 0 > index or index > len(reduction_dataframe):
                            notice = wrong_index()
                            error = True
                    else:
                        notice = wrong_index()
                        error = True

                if not error:
                    if len(reduction_dataframe) <= 1:
                        os.remove(path_reduction_character)
                    else:
                        reduction_dataframe = reduction_dataframe.drop(index)
                        reduction_dataframe.to_csv(path_reduction_character, index=False)
        # 一个指令或没有指令, 打印减伤列表
        elif not command2.matched:
            # 无buff错误输出
            if reduction_dataframe is None:
                notice = no_buff(character_name)
                error = True
            else:
                reduction_range_name = None
                count = 0
                send_list = []
                content = f'{character_name}共有{len(reduction_dataframe)}个资源变化修饰'
                # 如果有属性输入
                if command1.matched:
                    cmd1 = str(command1.result)
                    # 如果输入的是一个大类
                    if cmd1 in r_en_to_cn:
                        # 把中文输入换成英文
                        if cmd1 in r_en_to_cn.values():
                            for key, value in r_en_to_cn.items():
                                if value == reduction_range_name:
                                    reduction_range_name = key
                                    break
                        elif cmd1 in r_every:
                            for element in r_every:
                                if cmd1 == element:
                                    reduction_range_name = element
                    else:
                        notice = wrong_range(cmd1)
                        error = True
                if not error:

                    for index, data in reduction_dataframe.iterrows():

                        reduction_index = f'[{index + 1}]'
                        reduction_source = f"{data['source']}"
                        reduction_range = data['range']
                        defence = data['defence']

                        # 计算总共受到影响的属性，如果属性与r_every中的某一项相同，则将其提取出来
                        reduction_range_list = [range_item for range_item in r_every if range_item == reduction_range]
                        # 没有属性就跳出循环
                        if reduction_range_name is not None:
                            # 属性不在range中
                            if reduction_range_name not in reduction_range_list:
                                continue

                        count += 1

                        '''
                        '# buff range 换为中文
                        if reduction_range in r_en_to_cn:
                            reduction_range = r_en_to_cn[reduction_range]
                        '''

                        buff_value = data['value']

                        buff_type = data['type']

                        # 最终美化
                        insert = chr(12288)
                        dash = '—'
                        if defence == 1:
                            reduction_source = f"🛡{reduction_source}"
                        else:
                            reduction_source = f"📍{reduction_source}"
                        reduction_range = f"🏷{reduction_range}"
                        buff_type = f"{buff_type}"
                        buff_value = f"{buff_value}"

                        send_list.append(
                            f"{reduction_index:<}"
                            f"{reduction_source:{insert}<8}|"
                            f"{buff_value:^8}"
                            f"\n"
                            f"---"
                            f"{reduction_range:{dash}<8}"
                            f"{buff_type:{insert}>4}")

                    if command1.matched and count == 0:
                        content = f'{character_name}的[{reduction_range_name}]没有资源变化修饰'
                    elif command1.matched:
                        content = f'{character_name}的[{reduction_range_name}]共有{count}个资源变化修饰'
                    content = content + '\n' + "\n".join(send_list)
                    # 属性下没有buff

                    notice = content

    await app.send_message(sender, MessageChain(notice))

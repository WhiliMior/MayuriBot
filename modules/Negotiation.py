import codecs
import math
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
from graia.ariadne.util.saya import listen, dispatch

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.neg {rp评分} 进行交涉
.neg {对象等级} {对象智力%} 设定交涉对象
.neg {rp评分} {对象等级} {对象智力%} 设定交涉对象并交涉
    交涉不会受到任何buff影响
"""

buffed = '[↑]'


def no_chr(player):
    return f'{player}还没有角色×'


def check_success():
    return f'🎉成功！'


def check_failure():
    return f'❗️失败！'


target_level_name = '交涉对象等级'
target_intelligence_name = '交涉对象智力'

# 监听指令并回复
regular_expression = regex.Negotiation
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command3" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def Negotiation(app: Ariadne, sender: Sender, target: Target,
                      command1: RegexResult, command2: RegexResult, command3: RegexResult):
    player_id = target.id
    group_id = sender.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character_adv = p.path_file_character_adv
    path_file_character = p.path_file_character

    g = game_data.Group(group_id)
    path_group_file_neg = g.path_group_file_neg

    notice = 'error'
    error = True
    # 默认无角色错误输出
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    else:
        attri_dict_adv = toolkits.json_to_dict(path_file_character_adv)
        negotiation_buff = attri_dict_adv['buff_negotiation']
        attri_dict_basic = toolkits.json_to_dict(path_file_character)
        level = attri_dict_basic['level']

        def read_attribute_target(element):
            if os.path.exists(path_group_file_neg) is False:
                return None
            else:
                f = codecs.open(path_group_file_neg, 'r', 'utf-8')
                lines = f.readlines()
                for line in lines:
                    if element in line:
                        reg_ex = '-?[0-9]{1,}[.]?[0-9]*'
                        check = toolkits.check_string(reg_ex, line)
                        if check:
                            # 输出一个只包含单个属性数字的列表，然后转换成str
                            return float(''.join(re.findall(reg_ex, line)))
                        else:
                            return float(0)
                f.close()

        # 处理数字
        def str_number(number):
            return str(format(number, '.0f'))

        def int_number(number):
            return int(format(number, '.0f'))

        # 写入数值,attribute应为list
        def write_value(attributes):
            f = codecs.open(path_group_file_neg, 'w', 'utf-8')
            for line in attributes:
                f.write('%s\n' % line)
            f.close()

        # 写入等级和智力
        def write_target_attribute(number1, number2):
            target_level = str_number(float(number1))
            target_intelligence = str_number(float(number2))
            content = [target_level_name + target_level, target_intelligence_name + target_intelligence]
            write_value(content)

        # 给出默认分数0
        rp_grade = 0
        if command3.matched:
            cmd1 = str(command1.result)
            cmd2 = str(command2.result)
            cmd3 = str(command3.result)
            rp_grade = float(cmd1)
            write_target_attribute(cmd2, cmd3)
        elif command2.matched:
            cmd1 = str(command1.result)
            cmd2 = str(command2.result)
            write_target_attribute(cmd1, cmd2)
        elif command1.matched:
            cmd1 = str(command1.result)
            rp_grade = float(cmd1)

        # 检查是否有数据
        if os.path.exists(path_group_file_neg) is False \
                or read_attribute_target(target_level_name) is None \
                or read_attribute_target(target_intelligence_name) is None:
            notice = '没有交涉对象！'
        else:
            target_level = read_attribute_target(target_level_name)
            target_intelligence = read_attribute_target(target_intelligence_name)
            success_rate = int_number(((rp_grade + negotiation_buff) / target_intelligence * 10)
                                      * (math.log(level / target_level, math.e) + 1))
            if success_rate <= 0:
                success_rate = 0
            elif success_rate >= 100:
                success_rate = 100
            random_number = random.randint(1, 100)

            if random_number > success_rate:
                check_result = check_failure()
            else:
                check_result = check_success()

            if command3.matched or command1.matched and not command2.matched:
                notice = f'[{character_name}]' + '进行交涉检定' + '\n' + \
                         'RP：' + str_number(rp_grade) + '\n' + \
                         '成功率：' + str_number(success_rate) + '%' + '\n' + \
                         '检定：' + str(random_number) + '/' + str(success_rate) + '\n' + \
                         check_result
            elif command2.matched:
                notice = '已设定交涉对象！'
            else:
                notice = '请正确输入.ne指令！'

    await app.send_message(sender, MessageChain(notice))

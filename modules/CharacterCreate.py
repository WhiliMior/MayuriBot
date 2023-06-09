import csv
import os
import re

import pandas as pd
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.base import MatchRegex
from graia.ariadne.util.saya import listen, decorate

from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
CreateCharacter完成通知
input: 对象
output: str
"""


def get_notice(character):
    character_name = character.name
    send = f'[{character_name}] 的TL属性设置完成√'
    return send


# 创建角色, 返还一个对象
def character_create(sender, msg):
    # 字段分隔
    end_divider = ','
    middle_divider = ':'

    # 删除开头
    pattern = re.compile(r'^(^([.]|[。])TLsetup?)', re.I)
    full_text = str(pattern.sub('', msg).strip())
    # 将文本变成list
    attribute_list = full_text.split(end_divider)

    # 创建一个字典，然后将属性写入其中
    attribute_dict = {}
    for element in attribute_list:
        two_values = element.split(middle_divider)
        attribute = two_values[0]
        value = two_values[1]
        # 属性为空则用0替代
        if len(value) == 0:
            value = 0
        if toolkits.is_number(value):
            value = float(value)
        attribute_dict[attribute] = value

    character_attributes_cn = game_data.AttributesList.basic_cn
    character_attributes_cn_en_dict = game_data.AttributesList.basic_cn_to_en

    # 开始创建角色
    class Character:

        def __init__(self, player):
            self.player = player
            self.type = 'character'

    c = Character(sender)
    for element in character_attributes_cn:
        key_en = character_attributes_cn_en_dict.get(element)
        value = attribute_dict.get(element)
        setattr(c, str(key_en), value)
    # 返回一个实例对象
    return c


# 监听指令并回复
regular_expression = regex.CharacterCreate


@listen(GroupMessage, FriendMessage)
@decorate(MatchRegex(regex=regular_expression))
async def CreateCharacter(app: Ariadne, sender: Sender, target: Target,
                          msg: MessageChain):
    player_id = target.id
    msg_plain = msg.display
    # 创建一个角色实例
    c = character_create(player_id, msg_plain)
    json_c = toolkits.obj_to_json(c)
    character_name = c.name
    # 创建玩家对象
    p = game_data.Player(player_id, character_name)
    player_folder = p.path_folder_player
    character_file = p.path_file_character
    character_file_adv = p.path_file_character_adv
    # 检查文件夹, 写入角色basic和adv数据
    toolkits.check_folder(player_folder)
    toolkits.write_file(character_file, json_c)
    # 计算详细数据
    c_adv = game_data.create_advanced_attributes(c)
    json_c_adv = toolkits.obj_to_json(c_adv)
    toolkits.write_file(character_file_adv, json_c_adv)
    # 储存玩家信息
    player_file = p.path_file_player
    character_code = p.character_code
    header = ['player', 'character', 'code', 'using']
    player_list = [player_id, character_name, character_code, 1]

    if os.path.exists(player_file):
        csv_file = open(player_file, 'r', newline='', encoding='utf-8-sig', errors='ignore')
        player_dataframe = pd.read_csv(csv_file, header=0, sep=',')
        csv_file.close()
        # 检测是否已有角色
        if character_name not in player_dataframe['character'].values:
            player_dataframe['using'] = player_dataframe['using'].replace(1, 0)
            player_dataframe.loc[-1] = player_list
        player_dataframe.to_csv(player_file, index=False)
    else:
        csv_file = open(player_file, 'w', newline='', encoding='utf-8-sig', errors='ignore')
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerow(player_list)
    # 读取notice, 然后发送回复消息
    notice = get_notice(c)
    await app.send_message(sender, MessageChain(notice))

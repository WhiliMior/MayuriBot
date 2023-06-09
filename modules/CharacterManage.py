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

"""
.chr 显示现有角色
.chr {序号} 选择角色
.chr show 显示角色属性
.chr del {序号} 删除选定角色
"""


def select(character_name):
    return f'已选择角色 [{character_name}]√'


def delete(character_name):
    return f'已删除角色 [{character_name}]√'


def no_chr(player):
    return f'{player}还没有角色×'


# 监听指令并回复
regular_expression = regex.CharacterManage
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def ManageCharacter(app: Ariadne, sender: Sender, target: Target,
                          command1: RegexResult, command2: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    player_dataframe = p.player_dataframe
    player_file = p.path_file_player

    # 默认错误输出
    notice = "error"
    if not p.get_character():
        notice = no_chr(player_id)
    else:
        cmd1 = str(command1.result)
        cmd2 = str(command2.result)

        # 给指令-1, 并且限位
        def get_index(s):
            index = int(s) - 1
            if index <= 0:
                return 0
            elif index >= len(player_dataframe):
                return int(len(player_dataframe) - 1)
            else:
                return index

        # 有两个指令时
        if command2.matched:
            # del 删除角色
            if toolkits.check_string('del', cmd1):
                index = get_index(cmd2)
                character_name = player_dataframe.at[index, 'character']
                character_using = player_dataframe.at[index, 'using']
                p = game_data.Player(player_id, character_name)
                character_file = p.path_file_character
                character_file_adv = p.path_file_character_adv
                character_file_crd = p.path_file_character_crd
                character_file_weapon = p.path_weapon_character
                character_file_buff = p.path_buff_character
                character_file_reduction = p.path_reduction_character
                if len(player_dataframe) <= 1:
                    try:
                        os.remove(player_file)
                        os.remove(character_file)
                        os.remove(character_file_adv)
                        os.remove(character_file_crd)
                        os.remove(character_file_weapon)
                        os.remove(character_file_buff)
                        os.remove(character_file_reduction)
                    finally:
                        notice = delete(character_name)
                else:
                    if character_using == 1:
                        player_dataframe.loc[0, 'using'] = 1
                    player_dataframe = player_dataframe.drop(index)
                    player_dataframe.to_csv(player_file, index=False)
                    try:
                        os.remove(character_file)
                        os.remove(character_file_adv)
                        os.remove(character_file_crd)
                        os.remove(character_file_weapon)
                        os.remove(character_file_buff)
                        os.remove(character_file_reduction)
                    finally:
                        notice = delete(character_name)
        # 有一个指令时
        elif command1.matched:
            # show 展示角色
            if toolkits.check_string('show', cmd1):
                using_index = player_dataframe["using"].idxmax()
                character_name = player_dataframe.at[using_index, 'character']
                # 创建玩家对象
                p = game_data.Player(player_id, character_name)
                character_file = p.path_file_character
                character_file_adv = p.path_file_character_adv
                c = toolkits.json_to_obj(character_file)
                c_adv = toolkits.json_to_obj(character_file_adv)
                c_dict = c.__dict__
                c_adv_dict = c_adv.__dict__
                c_dict_all = {**c_dict, **c_adv_dict}
                # 去掉两个无用属性
                c_dict_all.pop('player')
                c_dict_all.pop('type')

                full_en_to_cn = game_data.AttributesList.full_en_to_cn
                # 全cn属性名
                full_list = full_en_to_cn.values()
                c_list = c_dict_all.values()
                # 替换为中文属性
                c_dict_all = dict(zip(full_list, c_list))

                send = ""
                # loop through the attributes in the attribute_dict dictionary
                insert = '—'
                for key, value in c_dict_all.items():
                    # check if the value is a number
                    send += f'{key:{insert}<7}: {str(value):<}\n'
                notice = send
            # 数字选择角色
            elif toolkits.is_number(cmd1):
                index = get_index(cmd1)
                player_dataframe['using'] = player_dataframe['using'].replace(1, 0)
                # 替换当前角色using为1
                player_dataframe.loc[index, 'using'] = 1
                player_dataframe.to_csv(player_file, index=False)

                character_name = player_dataframe.at[index, 'character']
                notice = select(character_name)
        # 没有其他指令, list角色
        elif not command2.matched and not command1.matched:
            send_list = []
            content = f'您共有{len(player_dataframe)}个角色'
            for index, data in player_dataframe.iterrows():
                if data[-1] == 0:
                    using = f'[{index + 1}]'
                else:
                    using = '[●]'
                send_list.append(f'{("{} {}".format(using, data[1]))}')
            content = content + '\n' + "\n".join(send_list) + '\n' + '请在指令后使用索引数字来更改角色选择'
            notice = content
    await app.send_message(sender, MessageChain(notice))

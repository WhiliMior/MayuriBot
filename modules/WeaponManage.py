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

from modules import WeaponCreate
from modules.tools import game_data, toolkits, regex
from modules.tools.toolkits import Sender, Target

"""
.wp 显示现有角色
.wp {序号} 选择角色
.wp show 显示角色属性
.wp del {序号} 删除选定角色
"""


def select(character_name):
    return f'已选择武器"{character_name}"√'


def delete(weapon_name):
    return f'已删除武器"{weapon_name}"√'


def no_chr(player):
    return f'{player}还没有角色×'


def no_weapon(character):
    return f'{character}还没有武器×'


# 监听指令并回复
regular_expression = regex.WeaponManage
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE),
    "command2" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def ManageWeapon(app: Ariadne, sender: Sender, target: Target,
                       command1: RegexResult, command2: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    weapon_dataframe = p.weapon_dataframe
    weapon_file = p.path_weapon_character

    # 默认错误输出
    notice = "error"
    if not p.get_character():
        notice = no_chr(player_id)
    # 没有武器
    elif not os.path.exists(weapon_file):
        notice = no_weapon(character_name)
    else:
        cmd1 = str(command1.result)
        cmd2 = str(command2.result)

        # 给指令-1, 并且限位
        def get_index(s):
            index = int(s) - 1
            if index <= 0:
                return 0
            elif index >= len(weapon_dataframe):
                return int(len(weapon_dataframe) - 1)
            else:
                return index

        # 有两个指令时
        if command2.matched:
            # del 删除武器
            if toolkits.check_string('del', cmd1):
                index = get_index(cmd2)
                weapon_name = weapon_dataframe.at[index, 'name']
                weapon_using = weapon_dataframe.at[index, 'using']
                wp_weight = weapon_dataframe.at[index, 'weight']
                if len(weapon_dataframe) <= 1:
                    os.remove(weapon_file)
                else:
                    if weapon_using == 1:
                        weapon_dataframe.loc[0, 'using'] = 1
                    weapon_dataframe = weapon_dataframe.drop(index)
                    weapon_dataframe.to_csv(weapon_file, index=False)

                # 修改负重
                path_file_character = p.path_file_character
                path_file_character_adv = p.path_file_character_adv
                # 添加负重到角色
                attri_dict = toolkits.json_to_dict(path_file_character)
                current_weight = attri_dict['weight']
                # 求和weapon weight
                weapon_weight = -wp_weight
                # 添加到人物
                character_weight = current_weight + weapon_weight
                # 重新计算高级属性
                result_notice = p.change_weight(weapon_weight)

                notice = delete(weapon_name) + '\n' + result_notice
        # 有一个指令时
        elif command1.matched:
            # show 展示武器
            if toolkits.check_string('show', cmd1):
                using_index = weapon_dataframe["using"].idxmax()
                weapon_list = weapon_dataframe.iloc[using_index].fillna('').tolist()
                wp_type = weapon_list[1]
                wp_attribute = weapon_list[2]
                # 换为中文
                type_list_en_to_cn = WeaponCreate.type_list_en_to_cn
                if wp_type in type_list_en_to_cn:
                    weapon_list[1] = type_list_en_to_cn[wp_type]
                # 十一个属性
                a = game_data.AttributesList
                basic_en_to_cn = a.basic_en_to_cn
                if wp_attribute in basic_en_to_cn:
                    weapon_list[2] = basic_en_to_cn[wp_attribute]

                header_cn = WeaponCreate.header_cn
                wp_dict_all = dict(zip(header_cn, weapon_list))

                # 删除为value为空的key
                wp_dict_all = {k: v for k, v in wp_dict_all.items() if v != ''}
                # 删除最后一个value
                wp_dict_all.popitem()

                send = ""
                # loop through the attributes in the attribute_dict dictionary
                insert = '—'
                for key, value in wp_dict_all.items():
                    # check if the value is a number
                    send += f'{key:{insert}<4}: {str(value):<}\n'
                notice = send
            # 数字选择武器
            elif toolkits.is_number(cmd1):
                index = get_index(cmd1)
                weapon_dataframe['using'] = weapon_dataframe['using'].replace(1, 0)
                # 替换当前角色using为1
                weapon_dataframe.loc[index, 'using'] = 1
                weapon_dataframe.to_csv(weapon_file, index=False)

                weapon_name = weapon_dataframe.at[index, 'name']
                notice = select(weapon_name)
        # 没有其他指令, list角色
        elif not command2.matched and not command1.matched:
            send_list = []
            content = f'您共持有{len(weapon_dataframe)}个武器'
            for index, data in weapon_dataframe.iterrows():
                if data[-1] == 0:
                    using = f'[{index + 1}]'
                else:
                    using = '[●]'
                send_list.append(f'{("{} {}".format(using, data[0]))}')
            content = content + '\n' + "\n".join(send_list) + '\n' + '请在指令后使用索引数字来更改武器选择'
            notice = content

    await app.send_message(sender, MessageChain(notice))

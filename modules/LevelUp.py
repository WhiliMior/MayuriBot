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
.lv +{数字} 升级
.lv -{数字} 降级
"""


def no_chr(player):
    return f'{player}还没有角色×'


def input_not_number():
    return f'指令错误×\n' \
           f'指令必须为数字且携带正负号'


# 监听指令并回复
regular_expression = regex.LevelUp
twilight = Twilight(
    RegexMatch(regular_expression).flags(re.I).space(SpacePolicy.PRESERVE),
    "command1" @ ParamMatch(optional=True).space(SpacePolicy.PRESERVE)
)


@listen(GroupMessage, FriendMessage)
@dispatch(twilight)
async def LevelUp(app: Ariadne, sender: Sender, target: Target,
                  command1: RegexResult):
    player_id = target.id
    # 创建玩家obj, 并从文件找到角色, 由于缺少角色名, 则必须get character
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character = p.path_file_character
    path_file_character_adv = p.path_file_character_adv

    # 默认错误输出
    notice = "error"
    error = False
    if not p.get_character():
        notice = no_chr(player_id)
        error = True
    elif command1.matched:
        cmd1 = str(command1.result)
        if not toolkits.is_number(cmd1):
            notice = input_not_number
            error = True

        attri_dict_basic = toolkits.json_to_dict(path_file_character)
        level = attri_dict_basic['level']
        if cmd1.startswith('+'):
            level_new = level + abs(float(cmd1[1:]))
        elif cmd1.startswith('-'):
            level_new = level - abs(float(cmd1[1:]))
        else:
            level_new = level

        if level_new < 1:
            level_new = 1

        if not error:
            attri_dict_basic['level'] = level_new
            json_data = toolkits.dict_to_json(attri_dict_basic)
            toolkits.write_file(path_file_character, json_data)

            c = toolkits.json_to_obj(path_file_character)
            c_adv_new = game_data.create_advanced_attributes(c)

            attri_json = toolkits.obj_to_json(c_adv_new)
            toolkits.write_file(path_file_character_adv, attri_json)

            if level_new < level:
                change = '[↓]'
            elif level_new > level:
                change = '[↑]'
            else:
                change = '[=]'

            ratio = level_new / level
            ratio = int(toolkits.reserve_zero_decimals(ratio * 100)-100)
            if ratio > 0:
                ratio = f'+{ratio}'
            notice = f'[{character_name}]等级变更: {change}\n' \
                     f'{level}→{level_new}\n' \
                     f'全属性变更: {ratio}%'

    await app.send_message(sender, MessageChain(notice))

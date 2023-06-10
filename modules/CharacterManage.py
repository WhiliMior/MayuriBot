import os
import re
from io import BytesIO
from PIL import Image as Img
from PIL import ImageFont, ImageDraw

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
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


def get_character_picture(c_dict):
    img = Img.new('RGB', (750, 1536), (255, 255, 255))
    color = (0, 0, 0)
    font_size = 33
    draw = ImageDraw.Draw(img)

    def paste_picture(picture, coordination):
        img.paste(picture, coordination, picture)

    def write_text(content, coordination):
        font = ImageFont.truetype('msyh.ttc', font_size)
        draw.text(coordination, content, color, font=font)

    player_id = c_dict['player']
    p = game_data.Player(player_id, None)
    p.get_character()
    character_name = p.character_name
    path_file_character_crd = p.path_file_character_crd
    path_buff_character = p.path_buff_character
    path_reduction_character = p.path_reduction_character
    character_crd_dict = toolkits.json_to_dict(path_file_character_crd)

    # 角色姓名
    icon = Img.open('icons/Character.png')
    location = (76, 114)
    paste_picture(icon, location)

    name = c_dict['name']
    text = f'{name}'
    location = (126, 112)
    write_text(text, location)

    # 等级
    icon = Img.open('icons/Level.png')
    location = (76, 202)
    paste_picture(icon, location)

    level = int(c_dict['level'])
    text = f'等级：{level}'
    location = (126, 200)
    write_text(text, location)

    # 绘制基础信息的背景板
    x, y, w, h, r = 44, 268, 662, 262, 10
    rectangle_color = (80, 156, 254)

    # 绘制圆角矩形
    def draw_rectangle():
        draw.rectangle((x + r, y, x + w - r, y + h), fill=rectangle_color)
        draw.rectangle((x, y + r, x + w, y + h - r), fill=rectangle_color)
        draw.ellipse((x, y, x + 2 * r, y + 2 * r), fill=rectangle_color)
        draw.ellipse((x + w - 2 * r, y, x + w, y + 2 * r), fill=rectangle_color)
        draw.ellipse((x, y + h - 2 * r, x + 2 * r, y + h), fill=rectangle_color)
        draw.ellipse((x + w - 2 * r, y + h - 2 * r, x + w, y + h), fill=rectangle_color)

    draw_rectangle()
    # 物理信息橙色长方形
    x, y, w, h, r = 44, 574, 310, 360, 10
    rectangle_color = (244, 176, 132)
    draw_rectangle()

    # 思维信息蓝色长方形
    x, y, w, h, r = 396, 574, 310, 360, 10
    rectangle_color = (142, 169, 219)
    draw_rectangle()

    # 修正信息灰色长方形
    x, y, w, h, r = 44, 978, 310, 360, 10
    rectangle_color = (177, 177, 177)
    draw_rectangle()

    # 领域信息黄色长方形
    x, y, w, h, r = 396, 978, 310, 360, 10
    rectangle_color = (236, 178, 0)
    draw_rectangle()

    # 外貌
    icon = Img.open('icons/Appearence.png')
    location = (426, 287)
    paste_picture(icon, location)

    appearance = int(c_dict['appearance'])
    text = f'外貌：{appearance}'
    font_size = 28
    color = (255, 255, 255)
    location = (476, 288)
    write_text(text, location)

    # 资产
    icon = Img.open('icons/Wealth.png')
    location = (426, 348)
    paste_picture(icon, location)

    wealth = int(c_dict['wealth'])
    text = f'资产：{wealth}'
    location = (476, 350)
    write_text(text, location)

    # 年龄
    icon = Img.open('icons/Age.png')
    location = (426, 410)
    paste_picture(icon, location)

    age = int(c_dict['age'])
    adult_age = int(c_dict['adult_age'])
    adult_age = f'[{adult_age}]'
    text = f"年龄：" \
           f"{age:{' '}<4}" \
           f"{adult_age:{' '}>5}"
    location = (476, 412)
    write_text(text, location)

    # 体型
    icon = Img.open('icons/Size.png')
    location = (426, 471)
    paste_picture(icon, location)

    size = int(c_dict['size'])
    standard_size = int(c_dict['standard_size'])
    standard_size = f'[{standard_size}]'
    text = f"体型：" \
           f"{size:{' '}<4}" \
           f"{standard_size:{' '}>5}"
    location = (476, 474)
    write_text(text, location)

    # 种族
    icon = Img.open('icons/Race.png')
    location = (76, 298)
    paste_picture(icon, location)

    race = c_dict['race']
    text = f'种族：{race}'
    location = (126, 300)
    write_text(text, location)

    # 性别
    icon = Img.open('icons/Gender.png')
    location = (76, 380)
    paste_picture(icon, location)

    gender = c_dict['gender']
    text = f'性别：{gender}'
    location = (126, 380)
    write_text(text, location)

    # 职业
    icon = Img.open('icons/Job.png')
    location = (76, 462)
    paste_picture(icon, location)

    occupation = c_dict['occupation']
    text = f'职业：{occupation}'
    location = (126, 460)
    write_text(text, location)

    first_distance = 5
    second_distance = 0

    physical = int(c_dict['physical'])
    mental = int(c_dict['mental'])
    ability = int(c_dict['ability'])
    # 物理
    revised_physical = int(c_dict['revised_physical'])
    physical_percentage = int((physical / ability) * 100)
    physical_percentage = f'[{physical_percentage}%]'
    text = f"物理 " \
           f"{revised_physical:{' '}<{first_distance}}" \
           f"{physical_percentage:{' '}<{second_distance}}"
    location = (76, 602)
    write_text(text, location)

    # 思维
    revised_mental = int(c_dict['revised_mental'])
    mental_percentage = int((mental / ability) * 100)
    mental_percentage = f'[{mental_percentage}%]'
    text = f"思维 " \
           f"{revised_mental:{' '}<{first_distance}}" \
           f"{mental_percentage:{' '}<{second_distance}}"
    location = (426, 602)
    write_text(text, location)

    # 体力
    hp = int(toolkits.reserve_zero_decimals(character_crd_dict['hp']))
    full_hitpoint = int(toolkits.reserve_zero_decimals((c_dict['full_hitpoint'])))
    hp_stats = f'{hp}/{full_hitpoint}'
    hp_ratio = int((hp / full_hitpoint) * 100)
    hp_ratio = f'[{hp_ratio}%]'
    text = f"{hp_stats:{' '}<{first_distance}} " \
           f"{hp_ratio:{' '}<{second_distance}}"
    location = (76, 660)
    write_text(text, location)

    # 意志
    mp = int(toolkits.reserve_zero_decimals(character_crd_dict['mp']))
    full_willpower = int(toolkits.reserve_zero_decimals((c_dict['full_willpower'])))
    mp_stats = f'{mp}/{full_willpower}'
    mp_ratio = int((mp / full_willpower) * 100)
    mp_ratio = f'[{mp_ratio}%]'
    text = f"{mp_stats:{' '}<{first_distance}} " \
           f"{mp_ratio:{' '}<{second_distance}}"
    location = (426, 660)
    write_text(text, location)

    constitution = int(toolkits.reserve_zero_decimals(c_dict['check_constitution']))
    dexterity = int(toolkits.reserve_zero_decimals(c_dict['check_dexterity']))
    strength = int(toolkits.reserve_zero_decimals(c_dict['check_strength']))
    willpower = int(toolkits.reserve_zero_decimals(c_dict['check_willpower']))
    education = int(toolkits.reserve_zero_decimals(c_dict['check_education']))
    intelligence = int(toolkits.reserve_zero_decimals(c_dict['check_intelligence']))
    medicine_and_life_science = int(toolkits.reserve_zero_decimals(c_dict['check_medicine_and_life_science']))
    engineering_and_technology = int(toolkits.reserve_zero_decimals(c_dict['check_engineering_and_technology']))
    military_and_survival = int(toolkits.reserve_zero_decimals(c_dict['check_military_and_survival']))
    literature = int(toolkits.reserve_zero_decimals(c_dict['check_literature']))
    visual_and_performing_art = int(toolkits.reserve_zero_decimals(c_dict['check_visual_and_performing_art']))

    def get_buffed_value(attribute):
        value, process = p.get_attribute_buffed(attribute)
        value = int(toolkits.reserve_zero_decimals(value))
        return value

    if os.path.exists(path_buff_character):
        constitution_buffed = get_buffed_value('体质')
        dexterity_buffed = get_buffed_value('敏捷')
        strength_buffed = get_buffed_value('力量')
        willpower_buffed = get_buffed_value('意志')
        education_buffed = get_buffed_value('教育')
        intelligence_buffed = get_buffed_value('智力')
        medicine_and_life_science_buffed = get_buffed_value('医学及生命科学')
        engineering_and_technology_buffed = get_buffed_value('工程与科技')
        military_and_survival_buffed = get_buffed_value('军事与生存')
        literature_buffed = get_buffed_value('文学')
        visual_and_performing_art_buffed = get_buffed_value('视觉及表演艺术')
    else:
        constitution_buffed = constitution
        dexterity_buffed = dexterity
        strength_buffed = strength
        willpower_buffed = willpower
        education_buffed = education
        intelligence_buffed = intelligence
        medicine_and_life_science_buffed = medicine_and_life_science
        engineering_and_technology_buffed = engineering_and_technology
        military_and_survival_buffed = military_and_survival
        literature_buffed = literature
        visual_and_performing_art_buffed = visual_and_performing_art

    def get_buff_amount(buffed, original):
        buff_amount = int(toolkits.reserve_one_decimals(buffed - original))
        if buff_amount > 0:
            buff_amount = f'(+{buff_amount})'
        elif buff_amount < 0:
            buff_amount = f'({buff_amount})'
        else:
            buff_amount = ''
        return buff_amount

    # 体质
    icon = Img.open('icons/Constitution.png')
    location = (76, 731)
    paste_picture(icon, location)
    buff_amount = get_buff_amount(constitution_buffed, constitution)

    text = f"体 " \
           f"{constitution_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (126, 726)
    write_text(text, location)

    # 敏捷
    icon = Img.open('icons/Dexterity.png')
    location = (76, 793)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(dexterity_buffed, dexterity)

    text = f"敏 " \
           f"{dexterity_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (126, 792)
    write_text(text, location)

    # 力量
    icon = Img.open('icons/Strengh.png')
    location = (76, 860)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(strength_buffed, strength)

    text = f"力 " \
           f"{strength_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (126, 858)
    write_text(text, location)

    # 意志
    icon = Img.open('icons/Willpower.png')
    location = (426, 726)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(willpower_buffed, willpower)

    text = f"意 " \
           f"{willpower_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 726)
    write_text(text, location)

    # 教育
    icon = Img.open('icons/Education.png')
    location = (426, 798)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(education_buffed, education)

    text = f"教 " \
           f"{education_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 792)
    write_text(text, location)

    # 智力
    icon = Img.open('icons/Intelligence.png')
    location = (426, 860)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(intelligence_buffed, intelligence)

    text = f"智 " \
           f"{intelligence_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 858)
    write_text(text, location)

    # 医学
    icon = Img.open('icons/Medical.png')
    location = (426, 1008)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(medicine_and_life_science_buffed, medicine_and_life_science)

    text = f"医 " \
           f"{medicine_and_life_science_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 1008)
    write_text(text, location)

    # 工程
    icon = Img.open('icons/Engineer.png')
    location = (426, 1074)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(engineering_and_technology_buffed, engineering_and_technology)

    text = f"工 " \
           f"{engineering_and_technology_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 1074)
    write_text(text, location)

    # 军事
    icon = Img.open('icons/Survival.png')
    location = (426, 1140)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(military_and_survival_buffed, military_and_survival)

    text = f"军 " \
           f"{military_and_survival_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 1140)
    write_text(text, location)

    # 文学
    icon = Img.open('icons/Literature.png')
    location = (426, 1205)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(literature_buffed, literature)

    text = f"文 " \
           f"{literature_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 1206)
    write_text(text, location)

    # 艺术
    icon = Img.open('icons/Art.png')
    location = (426, 1270)
    paste_picture(icon, location)

    buff_amount = get_buff_amount(visual_and_performing_art_buffed, visual_and_performing_art)

    text = f"艺 " \
           f"{visual_and_performing_art_buffed:{' '}<{first_distance}}" \
           f"{buff_amount:{' '}<{second_distance}}"
    location = (476, 1272)
    write_text(text, location)

    # 负重
    icon = Img.open('icons/Weight.png')
    location = (76, 1012)
    paste_picture(icon, location)

    weight = int(toolkits.reserve_zero_decimals(c_dict['weight']))
    full_weight = int(toolkits.reserve_zero_decimals(c_dict['full_weight']))
    text = f"负重 {weight}/{full_weight}"
    location = (126, 1008)
    write_text(text, location)

    # 负重修正
    revision_weight = c_dict['revision_weight']
    revision_weight = int(toolkits.reserve_zero_decimals(revision_weight * 100))
    text = f"修正 [{revision_weight}%]"
    location = (126, 1074)
    write_text(text, location)

    # 年龄修正
    icon = Img.open('icons/Age.png')
    location = (76, 1138)
    paste_picture(icon, location)

    # 物理年龄修正
    revision_age_physical = c_dict['revision_age_physical']
    revision_age_physical = int(toolkits.reserve_zero_decimals(revision_age_physical * 100))
    text = f"修正 [{revision_age_physical}%]"
    location = (126, 1140)
    color = (237, 125, 49)
    write_text(text, location)

    # 思维年龄修正
    revision_age_mental = c_dict['revision_age_mental']
    revision_age_mental = int(toolkits.reserve_zero_decimals(revision_age_mental * 100))
    text = f"修正 [{revision_age_mental}%]"
    location = (126, 1206)
    color = (68, 114, 196)
    write_text(text, location)

    # 体型修正
    icon = Img.open('icons/Size.png')
    location = (76, 1274)
    paste_picture(icon, location)

    revision_size = c_dict['revision_size']
    revision_size = int(toolkits.reserve_zero_decimals(revision_size * 100))
    text = f"修正 [{revision_size}%]"
    location = (126, 1272)
    color = (255, 255, 255)
    write_text(text, location)

    """
    # QQ
    icon = Img.open('icons/QQ.png')
    location = (76, 1474)
    paste_picture(icon, location)

    text = f"QID: 123456789"
    location = (126, 1476)
    color = (0, 0, 0)
    write_text(text, location)
    """

    img.save(f'cache/{player_id}.png')


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
                get_character_picture(c_dict_all)
                path = f"cache/{player_id}.png"
                notice = Image(path=path)
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

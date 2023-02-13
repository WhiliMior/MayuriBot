import math
import os
import codecs
import pandas as pd

from modules import Buff
from modules.tools import toolkits


def combine_lists_to_dict(a, b):
    # 把中英文对照塞进字典, 一一对应
    combined_dict = {}
    for x, y in zip(a, b):
        combined_dict[x] = y
    return combined_dict


# 所有的属性列表
class AttributesList:
    basic_en = ['name',
                'race',
                'adult_age',
                'standard_size',
                'age',
                'size',
                'appearance',
                'wealth',
                'gender',
                'occupation',
                'level',
                'physical_mental_ratio',
                'constitution',
                'dexterity',
                'strength',
                'willpower',
                'education',
                'intelligence',
                'medicine_and_life_science',
                'engineering_and_technology',
                'military_and_survival',
                'literature',
                'visual_and_performing_art',
                'weight']
    basic_cn = ['姓名',
                '种族',
                '成年年龄',
                '标准体型',
                '年龄',
                '体型',
                '外貌',
                '资产',
                '性别',
                '职业',
                '等级',
                '物理思维比值',
                '体质',
                '敏捷',
                '力量',
                '意志',
                '教育',
                '智力',
                '医学及生命科学',
                '工程与科技',
                '军事与生存',
                '文学',
                '视觉及表演艺术',
                '负重']
    basic_eleven_cn = ['体质',
                       '敏捷',
                       '力量',
                       '意志',
                       '教育',
                       '智力',
                       '医学及生命科学',
                       '工程与科技',
                       '军事与生存',
                       '文学',
                       '视觉及表演艺术', ]
    basic_cn_to_en = combine_lists_to_dict(basic_cn, basic_en)
    basic_en_to_cn = combine_lists_to_dict(basic_en, basic_cn)

    advanced_en = ['cash',
                   'full_hitpoint',
                   'full_willpower',
                   'ability',
                   'physical',
                   'mental',
                   'revision_age_physical',
                   'revision_age_mental',
                   'revision_size',
                   'revision_weight',
                   'full_weight',
                   'revised_physical',
                   'revised_mental',
                   'check_constitution',
                   'check_dexterity',
                   'check_strength',
                   'check_willpower',
                   'check_education',
                   'check_intelligence',
                   'check_medicine_and_life_science',
                   'check_engineering_and_technology',
                   'check_military_and_survival',
                   'check_literature',
                   'check_visual_and_performing_art',
                   'buff_negotiation']
    advanced_cn = ['现金',
                   '总_体力',
                   '总_意志',
                   '能力',
                   '物理',
                   '思维',
                   '修正_物理年龄',
                   '修正_思维年龄',
                   '修正_体型',
                   '修正_负重',
                   '总_负重',
                   '修正后_物理',
                   '修正后_思维',
                   '检定_体质',
                   '检定_敏捷',
                   '检定_力量',
                   '检定_意志',
                   '检定_教育',
                   '检定_智力',
                   '检定_医学及生命科学',
                   '检定_工程与科技',
                   '检定_军事与生存',
                   '检定_文学',
                   '检定_视觉及表演艺术',
                   '加成_交涉']
    advanced_cn_to_en = combine_lists_to_dict(advanced_cn, advanced_en)
    advanced_en_to_cn = combine_lists_to_dict(advanced_en, advanced_cn)
    full_en_to_cn = {**basic_en_to_cn, **advanced_en_to_cn}


a = AttributesList
advanced_en = a.advanced_en
advanced_cn_to_en = a.advanced_cn_to_en
advanced_en_to_cn = a.advanced_en_to_cn


def get_adv_cn_to_en(attribute):
    for key, value in advanced_cn_to_en.items():
        # 查找输入并转换为对应英文
        if attribute in key and '检定_' in key:
            attribute = value
            return attribute


# 通过创建玩家对象来获得玩家的数据, character_name为可选, 不填则自动读取角色csv找到当前角色
base_folder = 'data_tl_game'


class Player:

    def __init__(self, player_id, character_name):
        self.path_buff_character = None
        self.path_weapon_character = None

        self.buff_dataframe = None
        self.player_dataframe = None
        self.weapon_dataframe = None

        self.player = player_id
        self.path_folder_player = f'{base_folder}/player/{self.player}'
        self.path_file_player = f'{self.path_folder_player}/plr_{self.player}.csv'

        self.character_name = character_name
        if hasattr(self, 'character_name'):
            self.character_code = toolkits.encrypt_base64(character_name)

            self.path_file_character = f'{self.path_folder_player}/chr_{self.character_code}.json'
            self.path_file_character_adv = f'{self.path_folder_player}/chr_{self.character_code}_adv.json'
            self.path_file_character_crd = f'{self.path_folder_player}/chr_{self.character_code}_crd.json'

    def get_character(self):
        player_file = self.path_file_player
        # 打开玩家csv到dataframe
        if os.path.exists(player_file) is False:
            return False
        else:
            # 读取玩家的角色列表到csv
            csv_file = open(player_file, 'r', newline='', encoding='utf-8-sig', errors='ignore')
            self.player_dataframe = pd.read_csv(csv_file, header=0, sep=',')
            csv_file.close()

            using_index = self.player_dataframe["using"].idxmax()
            self.character_name = self.player_dataframe.at[using_index, 'character']
            self.character_code = self.player_dataframe.at[using_index, 'code']
            # 角色文档
            self.path_file_character = f'{self.path_folder_player}/chr_{self.character_code}.json'
            self.path_file_character_adv = f'{self.path_folder_player}/chr_{self.character_code}_adv.json'
            self.path_file_character_crd = f'{self.path_folder_player}/chr_{self.character_code}_crd.json'

            # 角色buff文档
            self.path_buff_character = f'{self.path_folder_player}/chr_{self.character_code}_buff.csv'
            self.path_weapon_character = f'{self.path_folder_player}/chr_{self.character_code}_weapon.csv'
            # buff 文档
            if os.path.exists(self.path_buff_character):
                # 读取角色的buff列表到csv
                csv_file = open(self.path_buff_character, 'r', newline='', encoding='utf-8-sig', errors='ignore')
                self.buff_dataframe = pd.read_csv(csv_file, header=0, sep=',')
                csv_file.close()
            # 武器文档
            if os.path.exists(self.path_weapon_character):
                # 获取dataframe
                csv_file = open(self.path_weapon_character, 'r', newline='', encoding='utf-8-sig', errors='ignore')
                self.weapon_dataframe = pd.read_csv(csv_file, header=0, sep=',')
                csv_file.close()

            return True

    # 输入中文, 获取属性数值
    def get_attribute_adv(self, attribute):
        attribute = get_adv_cn_to_en(attribute)
        # 没有属性
        if attribute is None:
            return None
        else:
            attri_dict = toolkits.json_to_dict(self.path_file_character_adv)
            attri_value = attri_dict[attribute]
            return attri_value

    def get_attribute_buffed(self, attribute):
        # 属性名和数值
        attri_name = get_adv_cn_to_en(attribute)
        # 没有属性
        if attri_name is None:
            return None
        else:
            attri_value = self.get_attribute_adv(attribute)
            # 定义四种type的总pool
            # 直接加算结果 = 直接加算A + 直接加算B + ...
            result_direct_add = 0
            # 直接乘算结果 = 直接乘算A + 直接乘算B + ...
            result_direct_time = 0
            # 最终加算结果 = 最终加算A + 最终加算B + ...
            result_final_add = 0
            # 最终乘算结果 = 最终乘算A * 最终乘算B * ...
            result_final_time = 0

            for index, data in self.buff_dataframe.iterrows():
                # 获取buff range
                buff_range = data['range']
                # 如果是大类
                if buff_range in Buff.r_en_to_list:
                    buff_range = Buff.r_en_to_list[buff_range]
                elif buff_range in advanced_en:
                    buff_range = [buff_range]
                # 判断输入的属性是否在buff range中, 不在就跳过该循环
                if attri_name not in buff_range:
                    continue

                # 开始计算
                buff_value = data['value']
                buff_type = data['type']
                # 判断buff type, 并计算
                if buff_type == 'direct_add':
                    result_direct_add += buff_value
                elif buff_type == 'direct_time':
                    result_direct_time += buff_value
                elif buff_type == 'final_add':
                    result_final_add += buff_value
                elif buff_type == 'final_time':
                    result_final_time += buff_value
            calculation_process = f'(({attri_value}+{result_direct_add})*(1+{result_direct_time})+{result_final_add})*(1+{result_final_time})'
            attri_buffed = ((attri_value + result_direct_add) * (
                    1 + result_direct_time) + result_final_add) * (1 + result_final_time)
            attri_buffed = toolkits.reserve_two_decimals(attri_buffed)

            return attri_buffed, calculation_process

    def change_weight(self, weight):
        attri_dict = toolkits.json_to_dict(self.path_file_character)
        current_weight = attri_dict['weight']
        weight_original = current_weight
        # 求和weapon weight
        change_weight = weight
        # 添加到人物
        character_weight = current_weight + change_weight
        weight_now = character_weight
        attri_dict['weight'] = character_weight
        # 写回去
        attri_json = toolkits.dict_to_json(attri_dict)
        toolkits.write_file(self.path_file_character, attri_json)

        # 计算详细数据
        c = toolkits.json_to_obj(self.path_file_character)
        c_adv = toolkits.json_to_obj(self.path_file_character_adv)
        revision_weight = c_adv.revision_weight
        full_weight = c_adv.full_weight
        check_dexterity = c_adv.check_dexterity
        c_adv_new = create_advanced_attributes(c)
        # 写入文件
        attri_json = toolkits.obj_to_json(c_adv_new)
        toolkits.write_file(self.path_file_character_adv, attri_json)

        revision_weight_new = c_adv_new.revision_weight
        full_weight_new = c_adv_new.full_weight
        check_dexterity_new = c_adv_new.check_dexterity

        notice = f'负重变更: {weight_original}→{weight_now}/{full_weight}\n' \
                 f'负重修正变更: {revision_weight}→{revision_weight_new}\n' \
                 f'敏捷变更: {check_dexterity}→{check_dexterity_new}'
        return notice


# 读取character中的basic属性
def read_basic_attribute(character, attribute_cn):
    dict = character.__dict__
    character_attributes_cn_en_dict = AttributesList.basic_cn_to_en
    attribute_en = character_attributes_cn_en_dict.get(attribute_cn)
    value = dict.get(attribute_en)
    return value


# 输入对象, 详细属性计算, 返还一个包含所有adv属性对象
def create_advanced_attributes(character):
    # 声明空字典
    attribute_dict = {}

    def add_attribute(key, value):
        if toolkits.is_number(value):
            value = float(value)
            value = toolkits.reserve_two_decimals(value)
        attribute_dict[key] = value

    # 计算现金
    wealth = read_basic_attribute(character, '资产')
    if wealth < 0:
        cash = (math.pow(wealth, 4) / math.pow(10, 4)) * -1
    else:
        cash = math.pow(wealth, 4) / math.pow(10, 4)
    add_attribute('现金', cash)

    # 计算能力
    level = read_basic_attribute(character, '等级')
    ability = level * 100
    add_attribute('能力', ability)

    # 计算物理
    ratio = read_basic_attribute(character, '物理思维比值')
    physical = ability - (ratio * level) / 10
    add_attribute('物理', physical)

    # 计算思维
    mental = ability - physical
    add_attribute('思维', mental)

    # 计算年龄修正
    age = read_basic_attribute(character, '年龄')
    adult_age = read_basic_attribute(character, '成年年龄')
    if adult_age == 0:
        revision_age_physical = 1
        revision_age_mental = 1
    else:
        revision_age_physical = math.cos(math.log(age / (adult_age * 1.5), math.e)) + 0.12
        if revision_age_physical <= 0:
            revision_age_physical = 0.01
        revision_age_mental = math.log(age / adult_age, 10) + 0.8
    add_attribute('修正_物理年龄', revision_age_physical)
    add_attribute('修正_思维年龄', revision_age_mental)

    # 计算体型修正
    size = read_basic_attribute(character, '体型')
    standard_size = read_basic_attribute(character, '标准体型')
    if standard_size == 0:
        revision_size = 1
    else:
        revision_size = math.log(size / standard_size, math.e) + 1
    if revision_size <= 0:
        revision_size = 0.01
    add_attribute('修正_体型', revision_size)

    # 计算修正后物理，体质
    revised_physical = physical * revision_age_physical
    add_attribute('修正后_物理', revised_physical)
    constitution = read_basic_attribute(character, '体质')
    check_constitution = revised_physical * constitution / 100 * revision_size
    add_attribute('检定_体质', check_constitution)

    # 计算体力
    full_hitpoint = format(check_constitution, '.0f')
    add_attribute('总_体力', full_hitpoint)

    # 计算力量
    strength = read_basic_attribute(character, '力量')
    check_strength = revised_physical * strength / 100 * revision_size
    add_attribute('检定_力量', check_strength)

    # 计算负重修正
    full_weight = check_strength * 10 / level
    weight = read_basic_attribute(character, '负重')
    revision_weight = -1 * math.pow(weight / full_weight, 2) + 1
    if revision_weight <= 0:
        revision_weight = 0.01
    add_attribute('总_负重', full_weight)
    add_attribute('修正_负重', revision_weight)

    # 计算敏捷
    dexterity = read_basic_attribute(character, '敏捷')
    check_dexterity = revised_physical * dexterity / 100 * revision_weight
    add_attribute('检定_敏捷', check_dexterity)

    # 计算思维
    revised_mental = mental * revision_age_mental
    add_attribute('修正后_思维', revised_mental)

    # def计算思维下副属性
    def mental_attribute_check(character, element):
        number = read_basic_attribute(character, element)
        element_check = revised_mental * number / 100
        return element_check

    check_willpower = mental_attribute_check(character, '意志')
    full_willpower = check_willpower
    add_attribute('检定_意志', check_willpower)
    add_attribute('总_意志', full_willpower)

    check_education = mental_attribute_check(character, '教育')
    check_intelligence = mental_attribute_check(character, '智力')
    add_attribute('检定_教育', check_education)
    add_attribute('检定_智力', check_intelligence)

    check_medicine_and_life_science = mental_attribute_check(character, '医学及生命科学')
    check_engineering_and_technology = mental_attribute_check(character, '工程与科技')
    check_military_and_survival = mental_attribute_check(character, '军事与生存')
    check_literature = mental_attribute_check(character, '文学')
    check_visual_and_performing_art = mental_attribute_check(character, '视觉及表演艺术')
    add_attribute('检定_医学及生命科学', check_medicine_and_life_science)
    add_attribute('检定_工程与科技', check_engineering_and_technology)
    add_attribute('检定_军事与生存', check_military_and_survival)
    add_attribute('检定_文学', check_literature)
    add_attribute('检定_视觉及表演艺术', check_visual_and_performing_art)

    # 计算交涉加成
    literature = read_basic_attribute(character, '文学')
    visual_and_performing_art = read_basic_attribute(character, '视觉及表演艺术')
    intelligence = read_basic_attribute(character, '智力')
    appearance = read_basic_attribute(character, '外貌')
    negotiation_buff = (literature + visual_and_performing_art + intelligence) * \
                       (math.log(mental / physical, 10) + 1) * \
                       (math.log(appearance / 50, math.e) + 1)
    add_attribute('加成_交涉', negotiation_buff)

    # 创建玩家crd文件
    hp_full = float(full_hitpoint)
    mp_full = full_willpower
    cash_origin = cash

    player = character.player
    character_name = character.name
    p = Player(player, character_name)
    path_file_character_crd = p.path_file_character_crd
    # 检查有没有先前的crd数据，没有就直接创建
    if not os.path.exists(path_file_character_crd):
        hp = hp_full
        mp = mp_full
        cash = cash_origin
    else:
        # 读取crd数据
        character_crd_dict = toolkits.json_to_dict(path_file_character_crd)

        # 获取crd数据中的值
        hp = character_crd_dict['hp']
        mp = character_crd_dict['mp']
        cash = character_crd_dict['cash']

        # 如果某项属性小于它的全量属性，则修改为等同于全量属性
        if hp > hp_full:
            hp = hp_full
        if mp > mp_full:
            mp = mp_full
        if cash > cash_origin:
            cash = cash_origin

    # 更新crd数据并写入文件
    crd_list_cn = ['hp', 'hp_full', 'mp', 'mp_full', 'cash', 'cash_origin']
    crd_list_value = [hp, hp_full, mp, mp_full, cash, cash_origin]
    # 保留一位小数
    crd_list_value = [toolkits.reserve_one_decimals(value) for value in crd_list_value]

    character_crd_dict = dict(zip(crd_list_cn, crd_list_value))
    crd_json = toolkits.dict_to_json(character_crd_dict)
    toolkits.write_file(path_file_character_crd, crd_json)

    # 添加属性
    class Character:

        def __init__(self, player):
            self.player = player
            self.type = 'character_adv'

    c = Character(character.player)

    character_attributes_cn = AttributesList.advanced_cn
    character_attributes_cn_en_dict = AttributesList.advanced_cn_to_en
    for element in character_attributes_cn:
        key_en = character_attributes_cn_en_dict.get(element)
        value = attribute_dict.get(element)
        setattr(c, str(key_en), value)

    return c


class Group:
    def __init__(self, group_id):
        self.group = group_id
        self.path_group_folder = f'{base_folder}/group/{self.group}'
        self.path_group_file_tar = f'{self.path_group_folder}/grp_tar_{self.group}.txt'
        self.path_group_file_bat = f'{self.path_group_folder}/grp_bat_{self.group}.csv'

    def get_tar(self):
        if os.path.exists(self.path_group_file_tar) is False:
            return None
        else:
            f = codecs.open(self.path_group_file_tar, 'r', 'utf-8')
            content = f.read()
            f.close()
            return int(content)

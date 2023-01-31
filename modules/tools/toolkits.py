import base64
import codecs
import json
import os
import re

from graia.ariadne.model import Friend, Group, Member

Sender = Group | Friend
Target = Member | Friend


# 判断是否为数字, 返回一个True False
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


# def保留两位小数
def reserve_two_decimals(number):
    # 返回一个float
    return float(format(number, '.2f'))


# def不保留小数
def reserve_zero_decimals(number):
    # 返回一个float
    return float(format(number, '.0f'))


# 字典转换为json
def dict_to_json(dict):
    json_data = json.dumps(dict, sort_keys=False, indent=4, ensure_ascii=False)
    return json_data


# 对象转换为json
def obj_to_json(obj):
    data = obj.__dict__
    json_data = dict_to_json(data)
    return json_data


# json转换为对象
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def json_to_dict(file):
    f = codecs.open(file, 'r+', 'utf-8')
    dict = eval(f.read())  # 读取的str转换为字典
    return dict


def json_to_obj(file):
    dict = json_to_dict(file)
    s = Struct(**dict)
    return s


# 加密字符
def encrypt_base64(string):
    string = str(string)
    code = str(base64.b64encode(string.encode()))
    rstr = r'[\'\/\\\:\*\?\"\<\>\|]'  # '/ \ : * ? " < > |'
    result = re.sub(rstr, "", code)  # 替换为空
    return result


# 如果没有文件夹则创建
def check_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


# 写文件
def write_file(path, content):
    f = codecs.open(path, 'w', 'utf-8')
    f.write(content)
    f.close()


# 检查正则
def check_string(re_exp, str):
    res = re.search(re_exp, str, re.I)
    if res:
        return True
    else:
        return False

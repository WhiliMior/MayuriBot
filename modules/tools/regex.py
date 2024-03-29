# 所有指令的指示符
headers = '([.]|[。])'
# 所有机器人控制指令的正则
BotControl = '^(\\[(.*?)\\]\\s)?([.]|[。])bot.*'
Dismiss = '^(\\[(.*?)\\]\\s)?([.]|[。])dismiss.*'
Help = '^([.]|[。])help.*'

# 所有游戏指令, (?i)忽略大小写
CharacterCreate = f'^{headers}TLsetup?.*'
CharacterManage = f'^{headers}ch[r]?'
DamageReduction = f'^{headers}dr?'
Target = f'^{headers}ta[r]?'
Buff = f'^{headers}bu[f]?[f]?'
WeaponCreate = f'^{headers}setupWP'
WeaponManage = f'^{headers}wp'
Examination = f'^{headers}ex'
Negotiation = f'^{headers}ne[g]?'
PreparationCheck = f'^{headers}pr[e]?'
Battle = f'^({headers}ba[t]?)'
Record = f'^{headers}crd'
LevelUp = f'{headers}lv'

# 骰子
RollDice = '^([.]|[。])[r].*'

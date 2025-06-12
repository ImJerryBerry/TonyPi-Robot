#!/usr/bin/python3
# coding=utf8
#app调用动作组对应字典，左为app调用，右为实际对应动作(dictionary mapping app calls to corresponding actions: Left side represents app calls, right side represents actual corresponding actions)
#在app里长按自定义即可进入输入模式，然后填写动作名称和编号，编号即为左边数字, 名称可随意起(in the app, long-press to enter custom mode, then fill in the action name and number. The number corresponds to the left side, and the name can be freely chosen)

action_group_dict = {
    '0': 'stand',           #立正(stand at attention)
    '1': 'go_forward',      #前进(go forward)
    '2': 'back_fast',       #后退(go backward)
    '3': 'left_move_fast',  #左移(move to left)
    '4': 'right_move_fast', #右移(move to right)
    '5': 'push_ups',        #俯卧撑(push-up)
    '6': 'sit_ups',         #仰卧起坐(sit-up)
    '7': 'turn_left',       #左转(turn left)
    '8': 'turn_right',      #右转(turn right)
    '9': 'wave',            #挥手(wave)
    '10': 'bow',            #鞠躬(bow)
    '11': 'squat',          #下蹲(squat)
    '12': 'chest',          #庆祝(celebration)
    '13': 'left_shot_fast', #左脚踢(left kick)
    '14': 'right_shot_fast',#右脚踢(right kick)
    '15': 'wing_chun',      #永春(Wing Chun)
    '16': 'left_uppercut',  #左勾拳(left hook)
    '17': 'right_uppercut', #右勾拳(right hook)
    '18': 'left_kick',      #左侧踢(left kick)
    '19': 'right_kick',     #右侧踢(right kick)
    '20': 'stand_up_front', #前跌倒起立(front fall and stand up)
    '21': 'stand_up_back',  #后跌倒起立(backward fall and stand up)
    '22': 'twist',          #扭腰(twist waist)
    '23': 'stand_slow',     #立正(stand at attention)
    '24': 'stepping',       #原地踏步(march in place)
    '25': 'jugong',         #鞠躬(bow)
    '35': 'weightlifting',  #举重(weightlifting)
    '36': 'jiandao',
    '37': 'shitou',
    '38': 'bu',
    '39': 'cry',
    '40': 'dance'
}

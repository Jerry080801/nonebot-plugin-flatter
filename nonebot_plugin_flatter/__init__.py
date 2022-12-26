from nonebot import get_driver, logger, on_command, on_fullmatch, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    PokeNotifyEvent,
    GroupMessageEvent,
)
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg, ArgStr

import random, emoji
from pathlib import Path
from typing import Literal

from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER
from pydantic import DurationError

try:
    import ujson as json
except ModuleNotFoundError:
    import json

def random_unit(p: float):
    if p == 0:
        return False
    if p == 1:
        return True

    R = random.random()
    if R < p:
        return True
    else:
        return False

'''
基础实现
1. 管理员开关用户的恭维,开关群内的恭维
2. 用户设置自己的恭维
3. 管理员清空用户的恭维
'''

superusers = get_driver().config.superusers

file_path = Path() / 'data' / 'flatter' / 'flatterlist.json'
file_path.parent.mkdir(parents=True, exist_ok=True)

flatterlist = (
    json.loads(file_path.read_text('utf-8'))
    if file_path.is_file()
    else {'grouplist': [], 'userlist': []}
)

def save_flatterlist() -> None:
    file_path.write_text(json.dumps(flatterlist), encoding='utf-8')

config_path = Path() / 'data' / 'flatter' / 'config.json'
config_path.parent.mkdir(parents=True, exist_ok=True)

config = (
    json.loads(config_path.read_text('utf-8'))
    if config_path.is_file()
    else {'trigger_chance': 10.0, 'admins': []}
)

def save_config() -> None:
    config_path.write_text(json.dumps(config), encoding='utf-8')

info_path = Path() / 'data' / 'flatter' / 'info.json'
info_path.parent.mkdir(parents=True, exist_ok=True)

info = (
    json.loads(info_path.read_text('utf-8'))
    if info_path.is_file()
    else {'': []}
)

def save_info() -> None:
    info_path.write_text(json.dumps(info), encoding='utf-8')

# 菜单和恭维列表
use_help = on_fullmatch('恭维')

@use_help.handle()

async def use_help_handle(bot: Bot, event: GroupMessageEvent):
    if (str(event.group_id) in flatterlist['grouplist']) and (str(event.user_id) in flatterlist['userlist']):
        if random.randint(0, 2) != 0:
            await use_help.send(
                '🌹 恭维 🌹\n' + 
                '数量 : 不限\n' +
                '长度 : 不限\n' +
                '几率 : ' + str(config['trigger_chance']) + '%\n' +
                '你的恭维是开启状态\n' + 
                '请文明用语⚡️本菜单和你的恭维列表将会随机返回'
                )
        else:
            # 发送恭维列表
            print('')
    elif str(event.group_id) in flatterlist['grouplist']:
        await use_help.send('🌹 恭维 🌹\n' + '数量 : 不限\n' +'长度 : 不限\n' +'几率 : ' + str(config['trigger_chance']) + '%\n' + '联系管理员进行开启,请勿多次触发\n' + '请文明用语⚡️本菜单和你的恭维列表将会随机返回')   

# 开启用户恭维
enable_flatter = on_command('恭维开启', aliases = {'开启恭维', '启用恭维'}, priority = 2, permission = SUPERUSER)

@enable_flatter.handle()

async def enable_flatter_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    try:
        segment_list = event.get_message()["at"]
        for i in [segment.data['qq'] for segment in segment_list]:
            flatterlist['userlist'].append(str(i))
    except:
        try:
            segment_list = str(arg.extract_plain_text().strip()).split(" ")
            for i in segment_list:
                flatterlist['userlist'].append(i) 
        except:
            logger.debug('根据at或者qq号添加恭维失败,请查看具体情况')
    save_flatterlist()
    await enable_flatter.send('已开启')

# 关闭用户恭维
disable_flatter = on_command('恭维关闭', aliases = {'关闭恭维', '停用恭维'}, priority = 2, permission = SUPERUSER)

@disable_flatter.handle()

async def disable_flatter_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    segment_list = event.get_message()["at"]
    try:
        for i in [segment.data['qq'] for segment in segment_list]:
            flatterlist['userlist'].remove(str(i))
        save_flatterlist()
    except:
        logger.debug('删除恭维列表失败,可能没设置qq')
    try:
        segment_list = str(arg.extract_plain_text().strip()).split(" ")
        for i in segment_list:
            flatterlist['userlist'].remove(i)
    except:
        logger.debug('删除恭维列表失败,可能没设置qq')
    await enable_flatter.send('已关闭')

# 开启本群恭维
enable_here = on_command('说话', aliases = {'开启本群恭维', '启用本群恭维'}, priority = 2, permission = SUPERUSER)

@enable_here.handle()

async def enable_here_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    flatterlist['grouplist'].append(str(event.group_id))
    save_flatterlist()
    await enable_flatter.send('已开启')

# 关闭本群恭维
disable_here = on_command('闭嘴', aliases = {'关闭本群恭维', '停用本群恭维'}, priority = 2, permission = SUPERUSER)

@disable_here.handle()

async def disable_here_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    try:
        flatterlist['grouplist'].remove(str(event.group_id))
        save_flatterlist()
        await enable_flatter.send('已关闭')
    except:
        logger.debug('没开吧')

# 设置几率
chance = on_command('恭维几率', aliases = {'设置恭维几率'}, priority = 2, permission = SUPERUSER)

@chance.handle()

async def chance_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    data = float(arg.extract_plain_text().strip())
    config['trigger_chance'] = data
    save_config()
    await chance.send('设置恭维触发的几率为' + str(data) + '%')

#主体
flatter = on_message(priority = 10, block = False)

@flatter.handle()

async def flatter_handle(bot: Bot, event: GroupMessageEvent):
    if (str(event.group_id) in flatterlist['grouplist']) and (str(event.user_id) in flatterlist['userlist']):
        if random_unit(float(config['trigger_chance']) / 100.0):
            #恭维
            data = info[str(event.user_id)]
            await bot.send_group_msg(group_id = event.group_id, message = data[random.randint(0, len(data) - 1)])

#用户设置信息

user_set = on_command('恭维', priority = 2)

@user_set.handle()

async def user_set_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    if (str(event.group_id) in flatterlist['grouplist']) and (str(event.user_id) in flatterlist['userlist']):
        data = str(arg.extract_plain_text().strip()).split('\n')
        info[str(event.user_id)] = data
        save_info()
        await user_set.send('已设置' + str(len(data)) + '条语句')

#管理设置信息

admin_set = on_command('设置用户', permission = SUPERUSER, priority = 2)

@admin_set.handle()

async def admin_set_handle(bot: Bot, event: GroupMessageEvent, arg: Message=CommandArg()):
    if (str(event.group_id) in flatterlist['grouplist']) and (str(event.user_id) in flatterlist['userlist']):
        data = str(arg.extract_plain_text().strip()).split(' ')
        uid = data[0]
        data.pop(0)
        info[uid] = data
        save_info()
        await user_set.send('已设置' + str(len(data)) + '条语句')


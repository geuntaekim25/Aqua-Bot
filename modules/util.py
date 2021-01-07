import discord
import json
import aiohttp
import sqlite3
import asyncio
from bs4 import BeautifulSoup
from modules.encrypt import EnDecrypt


def config():
    with open('config.json', 'r', encoding='utf-8-sig') as f:
        cfg = json.load(f)
    return cfg


async def determine_prefix(bot, message):
    cursor = sqlite3.connect('data.db').cursor()
    query = cursor.execute(f'SELECT * FROM prefix WHERE guild = "{message.guild.id}"').fetchone()

    if not query:
        return config()['prefix']
    else:
        return query[1]


async def send(bot, ctx, description):
    embed = discord.Embed(
        title="에러!",
        description=description,
        color=0xFF0000
    )
    embed.set_footer(
        text=bot.user.name,
        icon_url=bot.user.avatar_url
    )
    return await ctx.channel.send(ctx.author.mention, embed=embed)


async def cleanup(*args):
    for item in args:
        try:
            await item.delete()
        except:
            pass
    return None


async def get(url, headers=None, parse_type='default'):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if parse_type == 'default':
                text = await r.read()
                return BeautifulSoup(text, 'html.parser')
            else:
                text = await r.json()
                return text


def get_tags(ctx):
    cursor = sqlite3.connect('data.db').cursor()
    guild = cursor.execute(f'SELECT * FROM banned_tags WHERE guild = "{ctx.guild.id}"').fetchone()
    cursor.close()
    if not guild:
        return []
    return EnDecrypt(config()['key']).decrypt(guild[1])


def get_rank(value, sort='default'):
    cursor = sqlite3.connect('data.db').cursor()
    if sort == 'default':
        users = cursor.execute(f'SELECT * FROM user WHERE rank = "{value}"').fetchall()
        cursor.close()
        array = [int(user[0]) for user in users]
        return array
    else:
        user = cursor.execute(f'SELECT * FROM user WHERE user = "{value}"').fetchone()
        cursor.close()
        if not user:
            return 'default'
        return user[1]


async def save_bookmark(bot, ctx, mode, embed):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    bm_raw = cursor.execute(f'SELECT * FROM bookmarks WHERE '
                            f'user = "{ctx.author.id}" AND mode = "{mode}"').fetchall()
    key = EnDecrypt(config()['key'])
    bookmarks = []
    for bm in bm_raw:
        b = key.decrypt(bm[2])
        bookmarks.append(b)

    if mode == 'hitomi':
        art = embed.description.strip('[보러가기](https://hitomi.la/galleries/').strip('.html)')
    elif mode == 'nozomi':
        art = embed.description.strip('[보러가기](https://nozomi.la/post/').strip('.html)')
    elif mode in ['rule34', 'pixiv']:
        art = embed.description.strip('\n[보러가기](').strip(')')
    elif mode == 'anime':
        art = embed.title
    elif mode == 'hiyobi':
        art = embed.description.strip('[보러가기]((http://hiyobi.me/gallery/').strip(')')
    else:
        return

    if art in bookmarks:
        return await send(bot, ctx, "이미 북마크에 저장된 작품입니다.")

    data = [(ctx.author.id, mode, key.encrypt(art))]
    cursor.executemany("INSERT INTO bookmarks(user, mode, art) VALUES(?,?,?)", data)
    conn.commit()
    conn.close()
    embed = discord.Embed(description=f'해당 작품을 성공적으로 북마크에 저장했습니다.', color=0x00c062)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar_url)
    return await ctx.send(ctx.author.mention, embed=embed)


async def check_verify(bot, message):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    user = cursor.execute(f'SELECT * FROM verify WHERE user = "{message.author.id}"').fetchone()

    command_list = [await determine_prefix(bot, message) + str(cmd) for cmd in bot.commands]

    if message.author == bot.user or \
            message.content.split(' ')[0] not in command_list:
        return None

    if user is None:
        embed = discord.Embed(title="성인이신가요?", color=0xf04040,
                              description=f"{bot.user.mention}은 성인 전용 봇입니다.\n"
                                          f"성인이 맞다면 60초 내로 해당 메시지의 이모티콘을 클릭해주세요.\n"
                                          f"봇을 이용하는 것은 사용자 본인의 책임입니다.\n"
                                          f"이모티콘을 클릭하는 경우, 이에 동의하는 것으로 간주합니다.")
        msg = await message.channel.send(message.author.mention, embed=embed)
        await msg.add_reaction('⭕')
        try:
            await bot.wait_for(
                'reaction_add', timeout=60,
                check=lambda r, u: u == message.author and r.message.id == msg.id and str(r.emoji) == '⭕'
            )
        except asyncio.TimeoutError:
            return await msg.delete()

        cursor.execute(f'INSERT INTO verify VALUES ({message.author.id})')
        conn.commit()
        conn.close()
        await msg.delete()
        embed = discord.Embed(title="인증이 완료되었습니다.", color=0x00c062,
                              description="이제 봇의 모든 기능을 사용하실 수 있습니다.")
        return await message.channel.send(message.author.mention, embed=embed)
    conn.close()
    return await bot.process_commands(message)
import os
import sqlite3
import discord
from discord.ext import commands
from modules.util import config, determine_prefix, check_verify

bot = commands.Bot(command_prefix=determine_prefix, case_insensitive=True)
bot.remove_command("help")


@bot.event
async def on_message(message):
    if message.content == f"{config()['prefix']}초기화":
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM prefix WHERE guild = "{message.guild.id}"')
        conn.commit()
        conn.close()
        embed = discord.Embed(description=f'접두사가 초기화되었습니다.'
                                          f' 현재 접두사는 `{config()["prefix"]}`입니다.',
                              color=0x00c062)
        embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar_url)
        return await message.channel.send(message.author.mention, embed=embed)

    return await check_verify(bot, message)


for e in os.listdir('extensions'):
    if e == '__pycache__' or e.startswith('-'):
        continue
    try:
        bot.load_extension(f'extensions.{e.replace(".py", "")}')
    except Exception as error:
        print(f'{e} 로드 실패.\n{error}')

bot.run(config()['token'], bot=True, reconnect=True)

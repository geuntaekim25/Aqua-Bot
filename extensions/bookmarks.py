import sqlite3
import asyncio
import discord
from discord.ext import commands
from modules.encrypt import EnDecrypt
from modules.util import send, config, cleanup, determine_prefix
from modules.cooldown import CustomCooldown


class Bookmarks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def find_bookmarks(self, ctx, category, page, title):
        def list_split(n):
            for i in range(0, len(values), n):
                yield values[i:i + n]

        def check(m):
            if m.author != ctx.author or m.channel != ctx.channel:
                return None
            try:
                c = int(m.content.strip(config()['prefix']))
            except ValueError:
                return None
            if len(values) > c:
                return m.author == ctx.author and m.channel == ctx.channel

        try:
            page = int(page) - 1
        except ValueError:
            return await send(self.bot, ctx, "자연수를 입력해주세요.")

        cursor = sqlite3.connect('data.db').cursor()
        convert = {
            '히토미': 'hitomi',
            '노조미': 'nozomi',
            '픽시브': 'pixiv',
            '룰34': 'rule34',
            '애니': 'anime',
            '히요비': 'hiyobi'
        }

        if category and category in ['히토미', '노조미', '픽시브', '룰34', '애니', '히요비']:
            values = cursor.execute(f'SELECT * FROM bookmarks WHERE user = "{ctx.author.id}"'
                                    f' AND mode = "{convert[category]}"').fetchall()
        else:
            values = cursor.execute(f'SELECT * FROM bookmarks WHERE user = "{ctx.author.id}"').fetchall()

        if len(values) == 0:
            return await send(self.bot, ctx, "저장된 북마크가 없습니다.")
        elif len(values) == 1:
            return values[0]

        value_list = list(list_split(15))

        if 0 > page or page >= len(value_list):
            return await send(self.bot, ctx, f"입력하신 페이지({page + 1})가 너무 크거나 작습니다.")

        embeds = []
        count = 0
        for j in range(0, len(value_list)):
            bookmarks = '```\n'
            key = EnDecrypt(config()['key'])
            for value in values:
                bookmarks += f'{count}: {key.decrypt(value[2])}\n'
                count += 1
            bookmarks += '```'
            embed = discord.Embed(
                title=title,
                description=f"북마크의 좌측에 있는 숫자를 채팅창에 입력하세요."
                            f"\n{bookmarks}"
            )
            embed.set_footer(
                text=f'{j + 1} / {len(value_list)} | {self.bot.user.name}',
                icon_url=self.bot.user.avatar_url
            )
            embeds.append(embed)

        message = await ctx.send(ctx.author.mention, embed=embeds[page])
        try:
            respond = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await cleanup(message)

        await cleanup(message, respond)
        return values[int(respond.content.strip(config()['prefix']))]

    @commands.group(name='북마크', aliases=['bookmarks', 'b', 'bookmark'],
                    usage="`[목록/삭제]` `[카테고리]`",
                    description="저장된 작품을 불러오거나 삭제합니다.")
    @commands.check(CustomCooldown())
    async def bookmarks(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = await determine_prefix(self.bot, ctx)
            embed = discord.Embed(
                title="북마크",
                description=f"```\n"
                            f"{prefix}북마크 목록 [카테고리]\n"
                            f"{prefix}북마크 삭제 [카테고리]\n```",
                color=0xEEABBB
            )
            embed.add_field(name='카테고리', value='```\n전체, 히토미, 노조미, 픽시브, 룰34, 애니\n```')
            embed.set_footer(
                text=self.bot.user.name,
                icon_url=self.bot.user.avatar_url
            )
            return await ctx.send(ctx.author.mention, embed=embed)

    @bookmarks.command(name='목록', aliases=['list', 'l'])
    async def _list(self, ctx, category=None, page=1):
        value = await self.find_bookmarks(ctx, category, page, "불러올 북마크를 선택하세요.")
        if type(value) != tuple:
            return None

        param = EnDecrypt(config()['key']).decrypt(value[2])
        if value[1] == 'hitomi':
            await ctx.invoke(self.bot.get_command('히토미'), search=param)
        elif value[1] == 'nozomi':
            await ctx.invoke(self.bot.get_command('노조미'), search=param)
        elif value[1] == 'rule34':
            await ctx.invoke(self.bot.get_command('룰34'), query=param)
        elif value[1] == 'anime':
            await ctx.invoke(self.bot.get_command('애니'), query=param)
        elif value[1] == 'hiyobi':
            await ctx.invoke(self.bot.get_command('히요비'), search=param)
        elif value[1] == 'pixiv':
            await ctx.send(f'{ctx.author.mention}\n{param}')
        return

    @bookmarks.command(name='삭제', aliases=['delete', 'd'])
    async def delete(self, ctx, category=None, page=1):
        value = await self.find_bookmarks(ctx, category, page, "삭제할 북마크를 선택하세요.")
        if type(value) != tuple:
            return None

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM bookmarks WHERE user = "{ctx.author.id}"'
                       f' AND mode = "{value[1]}" AND art = "{value[2]}"')
        conn.commit()
        conn.close()
        embed = discord.Embed(description=f'북마크를 제거했습니다.', color=0x00c062)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        return await ctx.send(ctx.author.mention, embed=embed)


def setup(bot):
    bot.add_cog(Bookmarks(bot))

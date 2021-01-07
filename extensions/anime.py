import asyncio
import sqlite3
import discord
from discord.ext import commands
from modules.util import send, config, get, determine_prefix, cleanup
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_data(self, ctx, search):
        def replace_data(value):
            return value.lower().replace(' ', '').replace('♡', '').replace('-', '').replace('.', '') \
                .replace('!', '').replace('☆', '').replace('○', '').replace('~', '').replace('&', '') \
                .replace(':', '').replace('@', '').replace('#', '').replace('*', '').replace('(', '').replace(')', '') \
                .replace('+', '').replace('[', '').replace(']', '').replace('/', '').replace(',', '').replace('?', '') \
                .replace('`', '').replace('"', '').replace("'", "")

        def check(m):
            if m.author != ctx.author or m.channel != ctx.channel:
                return None
            try:
                c = int(m.content.strip(config()['prefix']))
            except ValueError:
                return None
            if len(queries) > c:
                return m.author == ctx.author and m.channel == ctx.channel

        cursor = sqlite3.connect('laftel.db').cursor()
        queries = cursor.execute(f'SELECT * FROM anime WHERE name LIKE "%{search}%"').fetchall()
        if not queries:
            anime_data = cursor.execute('SELECT * FROM anime').fetchall()
            for anime in anime_data:
                if replace_data(search) in replace_data(anime[1]):
                    queries = cursor.execute(f'SELECT * FROM anime WHERE name = "{anime[1]}"').fetchall()

        if len(queries) == 0:
            return await send(self.bot, ctx, "입력하신 애니는 존재하지 않습니다.")
        elif len(queries) == 1:
            return queries[0][0]

        content = '```\n'
        count = 0
        for query in queries:
            content += f"{count}: {query[1]}\n"
            count += 1
        content += '```'
        embed = discord.Embed(
            title="애니를 선택하세요.",
            description=f"애니메이션의 좌측에 있는 숫자를 채팅창에 입력하세요."
                        f"\n{content}"
        )
        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.avatar_url
        )
        message = await ctx.send(ctx.author.mention, embed=embed)
        try:
            respond = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await cleanup(message)
        await cleanup(message, respond)
        anime = queries[int(respond.content.strip(config()['prefix']))]
        return anime[0]

    @commands.command(name='애니', aliases=['a', 'anime'],
                      usage="`[제목]`", description="일본 애니메이션 정보를 불러옵니다.")
    @commands.check(CustomCooldown())
    async def anime(self, ctx, *, search=None):
        if search is None:
            return await send(self.bot, ctx, f"사용법: `{await determine_prefix(self.bot, ctx)}애니 [제목]`")

        index = await self.get_data(ctx, search)
        if type(index) != str:
            return None

        url = f'https://laftel.net/api/v1.0/items/{index}/detail/'
        header = {'laftel': 'TeJava'}
        await ctx.trigger_typing()
        js = await get(url, header, 'js')

        if js['is_ending'] is True:
            ending = '완결'
        else:
            ending = '방영중'

        embed = discord.Embed(title=js['name'], url=f'https://laftel.net/{index}',
                              description=f'{js["content_rating"]} | {ending}',
                              color=0x3361B6)

        if js['author']:
            authors = ''
            for a in js['author']:
                authors += f'{a["name"]}, '
            embed.add_field(name="작가", value=authors.strip(', '), inline=False)

        if js['illustrator']:
            illustrators = ''
            for a in js['illustrator']:
                illustrators += f'{a["name"]}, '
            embed.add_field(name="일러스트레이터", value=illustrators.strip(', '), inline=False)

        if js['main_tag']:
            tags = ''
            for t in js['main_tag']:
                tags += f'{t["name"]}, '
            embed.add_field(name="태그", value=tags.strip(', '), inline=False)

        if js['animation_info']['production']['name']:
            embed.add_field(name='제작', value=js['animation_info']['production']['name'], inline=False)
        if js['animation_info']['air_year_quarter']:
            embed.add_field(name='출시', value=js['animation_info']['air_year_quarter'], inline=False)
        if js['content']:
            embed.add_field(name='줄거리', inline=False,
                            value=js['content'].replace('\r\n', ''))
        embed.set_footer(text=self.bot.user.name,
                         icon_url=self.bot.user.avatar_url)
        embed.set_image(url=js['img'])
        msg = await ctx.send(ctx.author.mention, embed=embed)
        page = Paginator(self.bot, ctx, msg, embeds=[embed],
                         only=ctx.author, timeout=60, mode='anime')
        return await page.start()


def setup(bot):
    bot.add_cog(Anime(bot))

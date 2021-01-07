import io
import aiohttp
import discord
from discord.ext import commands
from nozomi import api
from modules.util import send, determine_prefix, get_tags
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Nozomi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='노조미', aliases=['n', 'nozomi'],
                      usage="`[URL 또는 번호]`", description="Nozomi.la 포스트 정보를 불러옵니다.")
    @commands.check(CustomCooldown())
    async def nozomi(self, ctx, *, search=None):
        if search is None:
            return await send(self.bot, ctx,
                              f"사용법: `{await determine_prefix(self.bot, ctx)}노조미 [URL 또는 번호]`")

        if 'nozomi.la' not in search:
            try:
                int(search)
            except ValueError:
                return await send(self.bot, ctx, "입력하신 작품은 존재하지 않습니다.")

            art_id = search.split(' ')[0]
        else:
            art_id = search.split('/')[-1].replace('.html', '')
            try:
                int(art_id)
            except ValueError:
                art_id = art_id.split('-')[-1]

        await ctx.trigger_typing()
        url = f'https://nozomi.la/post/{art_id}.html'
        post = await api.get_post(url)
        if post is None:
            return await send(self.bot, ctx, "입력하신 작품은 존재하지 않습니다.")

        tags = ''
        for i in post.general[:10]:
            tags += f'{i.tagname_display}\n'

        for t in tags.split('\n'):
            if t.lower() in get_tags(ctx):
                return await send(self.bot, ctx, "검색하신 작품에서 금지된 태그가 감지되었습니다.")

        if len(post.general) > 10:
            tags += '...'

        embed = discord.Embed(
            title='Nozomi.la',
            description=f'[보러가기](https://nozomi.la/post/{art_id}.html)',
            color=0xe29fc9)
        if post.artist:
            artists = ''
            for a in post.artist:
                artists += f'{a.tagname_display}\n'
            embed.add_field(name='아티스트', value=artists, inline=False)

        if post.copyright:
            series = ''
            for s in post.copyright:
                series += f'{s.tagname_display}\n'
            embed.add_field(name='시리즈', value=series, inline=False)

        if post.character:
            characters = ''
            for c in post.character:
                characters += f'{c.tagname_display}\n'
            embed.add_field(name='캐릭터', value=characters, inline=False)

        if tags != '':
            embed.add_field(name='태그', value=tags, inline=False)

        embed.add_field(name='업로드 날짜', value=post.date.split(' ')[0], inline=False)
        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.avatar_url)
        embed.set_image(url=post.imageurl)
        await ctx.send(ctx.author.mention, embed=embed)

        headers = {
            'Host': 'i.nozomi.la',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://nozomi.la/',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(post.imageurl, headers=headers) as resp:
                data = io.BytesIO(await resp.read())
        try:
            msg = await ctx.send(file=discord.File(data, 'image.png'))
        except discord.HTTPException:
            msg = await ctx.send(post.imageurl)

        page = Paginator(self.bot, ctx, msg, embeds=[embed],
                         only=ctx.author, timeout=60, mode='nozomi')
        await page.start()


def setup(bot):
    bot.add_cog(Nozomi(bot))

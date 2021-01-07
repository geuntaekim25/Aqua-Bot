import discord
from discord.ext import commands
import aiohttp
from modules.util import config, send, get, determine_prefix, get_tags
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Hitomi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='히토미', aliases=['h', 'hitomi'],
                      usage="`[URL 또는 번호]`",
                      description="Hitomi.la 갤러리 정보를 불러옵니다.")
    @commands.check(CustomCooldown())
    async def hitomi(self, ctx, *, search=None):
        if search is None:
            return await send(self.bot, ctx,
                              f"사용법: `{await determine_prefix(self.bot, ctx)}히토미 [URL 또는 번호]`")

        if 'hitomi.la' not in search:
            try:
                int(search)
            except ValueError:
                return await send(self.bot, ctx, "입력하신 작품은 존재하지 않습니다.")

            art_id = search.split(' ')[0]
        else:
            art_id = search.split('/')[-1].strip('.html')
            try:
                int(art_id)
            except ValueError:
                art_id = art_id.split('-')[-1]

        await ctx.trigger_typing()
        url = f'https://ltn.hitomi.la/galleryblock/{art_id}.html'
        try:
            soup = await get(url, config()['header'])
        except aiohttp.ClientConnectorError:
            return await send(self.bot, ctx, "HTTPS 우회 설정이 활성화되지 않았습니다.")

        colors = {
            'Artist CG': 0x99cccc,
            'Manga': 0xcc99cc,
            'Doujinshi': 0xcc9999,
            'Anime': 0x99cc99,
            'Game CG': 0x9999cc
        }

        title = soup.select_one('h1').string
        if title == '404 Not Found':
            return await send(self.bot, ctx, "입력하신 작품은 존재하지 않습니다.")

        try:
            artist = soup.select_one('div.artist-list > ul > li > a').string
        except AttributeError:
            artist = 'N/A'

        try:
            series = soup.select_one('div.dj-content > table > tr:nth-child(1) > td:nth-child(2)').string
        except AttributeError:
            series = 'N/A'

        art_type = soup.select_one('div.dj-content > table > tr:nth-child(2) > td:nth-child(2)'
                                   ).string.capitalize().replace('cg', 'CG')

        try:
            language = soup.select_one('table > tr:nth-child(3) > td:nth-child(2)').string.capitalize()
        except AttributeError:
            language = 'N/A'

        tag_str = ''
        tags = []
        try:
            count = 1
            while True:
                tag = soup.select_one(f'table > tr:nth-child(4) > td.relatedtags > ul > li:nth-child({count}) > a')
                if tag:
                    tag_str += f'{tag.string.title()}\n'
                    tags.append(tag.string.replace(' ', '').strip('♀').strip('♂'))
                else:
                    break
                count += 1
        except AttributeError:
            pass

        try:
            thumbnail = soup.select_one('div.dj-img1 > picture > img')['src']
        except TypeError:
            thumbnail = soup.select_one('div.cg-img1 > picture > img')['src']

        date = soup.select_one('div.dj-content > p').string

        for t in tags:
            t = t.lower().replace('female:', '').replace('male:', '').replace(' ', '')
            if t in get_tags(ctx):
                return await send(self.bot, ctx, "검색하신 작품에서 금지된 태그가 감지되었습니다.")

        embed = discord.Embed(
            title=title,
            description=f'[보러가기](http://hitomi.la/galleries/{art_id}.html)',
            color=colors[art_type])
        embed.add_field(name='아티스트', value=artist, inline=False)
        embed.add_field(name='타입', value=art_type, inline=False)
        embed.add_field(name='언어', value=language, inline=False)
        embed.add_field(name='시리즈', value=series, inline=False)
        embed.add_field(name='태그', value=tag_str, inline=False)
        embed.add_field(name='업로드 날짜', value=date.split(' ')[0], inline=False)
        embed.set_image(url='https:' + thumbnail)
        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.avatar_url)
        msg = await ctx.send(ctx.author.mention, embed=embed)
        page = Paginator(self.bot, ctx, msg, embeds=[embed],
                         only=ctx.author, timeout=60, mode='hitomi')
        return await page.start()


def setup(bot):
    bot.add_cog(Hitomi(bot))

import discord
from discord.ext import commands
from modules.util import config, send, get, determine_prefix, get_tags
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Hiyobi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='히요비', aliases=['hiyobi'],
                      usage="`[URL 또는 번호]`",
                      description="Hiyobi.me 갤러리 정보를 불러옵니다.")
    @commands.check(CustomCooldown())
    async def hiyobi(self, ctx, *, search=None):
        if search is None:
            return await send(self.bot, ctx,
                              f"사용법: `{await determine_prefix(self.bot, ctx)}히요비 [URL 또는 번호]`")

        if 'hiyobi.me' not in search:
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
        url = f'https://api.hiyobi.me/gallery/{art_id}'
        js = await get(url, config()['header'], 'js')

        if js['id'] == 0:
            return await send(self.bot, ctx, "입력하신 작품은 존재하지 않습니다.")

        colors = {
            1: 0xcc9999,
            2: 0xcc99cc,
            3: 0x99cccc,
            4: 0x9999cc,
            5: 0x99cc99,
        }
        convert = {
            1: '동인지',
            2: '망가',
            3: 'CG 아트',
            4: '게임 CG',
            5: '애니',
        }

        embed = discord.Embed(
            title=js['title'],
            description=f'[보러가기](http://hiyobi.me/gallery/{art_id})',
            color=colors[js['type']])

        if js['artists']:
            artists = ''
            for a in js['artists']:
                artists += f'{a["display"]}\n'
            embed.add_field(name='아티스트', value=artists, inline=False)

        if js['groups']:
            groups = ''
            for g in js['groups']:
                groups += f'{g["display"]}\n'
            embed.add_field(name='캐릭터', value=groups, inline=False)

        if js['parodys']:
            series = ''
            for s in js['parodys']:
                series += f'{s["display"]}\n'
            embed.add_field(name='시리즈', value=series, inline=False)

        if js['characters']:
            characters = ''
            for c in js['characters']:
                characters += f'{c["display"]}\n'
            embed.add_field(name='캐릭터', value=characters, inline=False)

        embed.add_field(name='타입', value=convert[js['type']], inline=False)

        tags = ''
        tags_raw = []
        for t in js['tags']:
            tags += f'{t["display"]}\n'
            tags_raw.append(t['value'])

        for t in tags_raw:
            t = t.lower().replace('female:', '').replace('male:', '')
            if t in get_tags(ctx):
                return await send(self.bot, ctx, "검색하신 작품에서 금지된 태그가 감지되었습니다.")

        if tags != '':
            embed.add_field(name='태그', value=tags, inline=False)

        embed.set_image(url='https://cdn.hiyobi.me/tn/' + art_id + '.jpg')
        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.avatar_url)
        msg = await ctx.send(ctx.author.mention, embed=embed)
        page = Paginator(self.bot, ctx, msg, embeds=[embed],
                         only=ctx.author, timeout=60, mode='hiyobi')
        return await page.start()


def setup(bot):
    bot.add_cog(Hiyobi(bot))

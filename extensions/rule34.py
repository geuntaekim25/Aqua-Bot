import discord
from discord.ext import commands
import aiohttp
import rule34
from modules.util import config, send, get, determine_prefix
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Rule34(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def wrap_embed(self, ctx, title, link, tags, thumbnail):
        embed = discord.Embed(title=title, color=0xACE4A3,
                              description=f'\n[보러가기]({link})')
        embed.add_field(name='태그', value=tags, inline=False)
        embed.set_image(url=thumbnail)
        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.avatar_url
        )
        msg = await ctx.send(ctx.author.mention, embed=embed)
        page = Paginator(self.bot, ctx, msg, embeds=[embed],
                         only=ctx.author, timeout=60, mode='rule34')
        return await page.start()

    @commands.command(name='룰34', aliases=['rule', 'rule34', '룰', 'r'],
                      usage="`[URL]`", description="Rule34 작품 정보를 불러옵니다.")
    @commands.check(CustomCooldown())
    async def rule(self, ctx, *, search=None):
        await ctx.trigger_typing()
        if search is None:
            return await send(self.bot, ctx,
                              f"사용법: `{await determine_prefix(self.bot, ctx)}룰34 [URL]`")

        elif 'rule34.paheal.net' in search:
            try:
                soup = await get(search, config()['header'])
            except aiohttp.ClientConnectorError:
                return await send(self.bot, ctx, "HTTPS 우회 설정이 활성화되지 않았습니다.")

            thumbnail = soup.select_one('#main_image')['src']
            tags = soup.select_one('#tag_editor')['value'].replace(' ', '\n').replace('_', ' ')
            return await self.wrap_embed(ctx, 'Rule34(Paheal)', search, tags, thumbnail)

        elif 'rule34.xxx' in search:
            art_id = search.split("=")[-1]
            r = rule34.Rule34()
            data = await r.getPostData(art_id)

            tags = data['@tags'].replace(' ', '\n').replace('_', ' ').title()
            if len(tags.split('\n')) > 15:
                tags = '\n'.join(tags.split('\n')[:15])
                tags += '\n...'

            url = f'https://rule34.xxx/index.php?page=post&s=view&id={art_id}'
            return await self.wrap_embed(ctx, 'Rule34', url, tags, data['@file_url'])

        else:
            return await send(self.bot, ctx, "링크를 입력해주세요.")


def setup(bot):
    bot.add_cog(Rule34(bot))

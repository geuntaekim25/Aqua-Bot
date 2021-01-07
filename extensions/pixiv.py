import discord
from discord.ext import commands
from pysaucenao import SauceNao
from pysaucenao import errors
from modules.util import config, send, determine_prefix
from modules.Pagination import Paginator
from modules.cooldown import CustomCooldown


class Pixiv(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='픽시브', aliases=['p', 'pixiv'],
                      usage="`[사진 URL 또는 첨부 사진]`",
                      description="Pixiv에서 이미지를 검색합니다.")
    @commands.check(CustomCooldown())
    async def p(self, ctx, *, search=None):
        async def get_data(link):
            await ctx.trigger_typing()
            sauce = SauceNao(db_mask=8191, api_key=config()['sauce_token'])
            try:
                results = await sauce.from_url(link)
            except errors.InvalidImageException:
                return await send(self.bot, ctx, "전송하신 이미지와 비슷한 일러스트를 찾을 수 없습니다.")
            except errors.DailyLimitReachedException:
                return await send(self.bot, ctx,
                                  "금일 검색 가능한 횟수를 모두 소진하였습니다. 내일 다시 시도해주세요.")

            if len(results) == 0:
                return await send(self.bot, ctx, "전송하신 이미지와 비슷한 일러스트를 찾을 수 없습니다.")

            thumbnail = results[0].thumbnail
            similarity = results[0].similarity
            title = results[0].title
            url = results[0].url
            author = results[0].author_name

            if float(similarity) < 80:
                return await send(self.bot, ctx, "전송하신 이미지와 비슷한 일러스트를 찾을 수 없습니다.")

            embed = discord.Embed(
                title=title,
                color=0x228d7f,
                description=f"[보러가기]({url})"
            )
            embed.add_field(name='아티스트', value=author, inline=False)
            embed.add_field(name='유사도', value=similarity, inline=False)
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(
                icon_url=self.bot.user.avatar_url,
                text=self.bot.user.name)
            msg = await ctx.send(ctx.author.mention, embed=embed)
            page = Paginator(self.bot, ctx, msg, embeds=[embed],
                             only=ctx.author, timeout=60, mode='pixiv')
            return await page.start()

        if search:
            if 'http' not in search:
                return await send(self.bot, ctx, "링크를 입력해주세요.")
            return await get_data(search)

        elif not search and len(ctx.message.attachments) > 0:
            await get_data(ctx.message.attachments[0].url)

        else:
            return await send(self.bot, ctx,
                              f"사용법: `{await determine_prefix(self.bot, ctx)}픽시브 [사진 URL 또는 첨부 사진]`")


def setup(bot):
    bot.add_cog(Pixiv(bot))

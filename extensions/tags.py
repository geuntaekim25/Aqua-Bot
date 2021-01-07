import sqlite3
import discord
from discord.ext import commands
from modules.encrypt import EnDecrypt
from modules.util import send, config, determine_prefix, get_rank


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.key = EnDecrypt(config()['key'])

    @commands.group(name='태그', aliases=['tags', 'tag', 't'],
                    usage="`[목록/추가/삭제]` `[태그 이름]`",
                    description="검색을 금지/허용할 태그를 지정합니다.")
    async def _tag(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = await determine_prefix(self.bot, ctx)
            embed = discord.Embed(
                title="태그",
                description=f"```\n"
                            f"{prefix}태그 목록\n"
                            f"{prefix}태그 추가 [태그 이름]\n"
                            f"{prefix}태그 삭제 [태그 이름]\n```",
                color=0xEEABBB
            )
            embed.add_field(name='주의사항',
                            value='금지 태그 기능은 히토미, 히요비, 노조미에서만 작동합니다.\n'
                                  '금지 태그의 추가/삭제로 발생하는 책임은 사용자 본인에게 있으며, '
                                  '디스코드 이용약관 및 아동·청소년의 성보호에 관한 법률을 준수하여 '
                                  '금지 태그를 추가/삭제 하시기를 권장드립니다.')
            embed.set_footer(
                text=self.bot.user.name,
                icon_url=self.bot.user.avatar_url
            )
            return await ctx.send(ctx.author.mention, embed=embed)

    async def get_tags(self, ctx, tag):
        cursor = sqlite3.connect('data.db').cursor()
        value = cursor.execute(f'SELECT * FROM banned_tags WHERE guild = "{ctx.guild.id}"').fetchone()
        if not value and not tag:
            return await send(self.bot, ctx, "저장된 태그가 존재하지 않습니다.")
        elif not value and tag:
            return ''

        tags = self.key.decrypt(value[1])

        if tag is None:
            tags_str = ', '.join(tags.split(','))
            embed = discord.Embed(title=f"`{ctx.guild.name}` 서버의 금지 태그", color=0x5a98d5,
                                  description=f'```\n{tags_str}```')
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
            return await ctx.send(ctx.author.mention, embed=embed)
        return tags

    @_tag.command(name='목록', aliases=['list', 'l'])
    async def _list(self, ctx):
        return await self.get_tags(ctx, None)

    @_tag.command(name='추가', aliases=['add', 'a'])
    async def add(self, ctx, *, tag=None):
        tags = await self.get_tags(ctx, tag)
        if type(tags) != str:
            return None

        tag = tag.lower().replace(' ', '').replace('female:', '')\
            .replace('male:', '').replace('여:', '').replace('남:', '')
        tags_list = [t for t in tags.split(',')]
        for t in tags_list:
            if tag == t:
                return await send(self.bot, ctx, "이미 등록된 태그입니다.")

        limit = {
            'mod': 999999,
            'patron': 999999,
            'voter': 10,
            'default': 5
        }

        rank = get_rank(ctx.author.id, 'user')
        if len(tags_list) >= limit[rank]:
            return await send(self.bot, ctx, f"금지 태그는 최대 {limit[rank]}개까지 등록할 수 있습니다.\n"
                                             f"봇에 하트를 눌러주시면 금지 태그를 최대 {limit['voter']}개까지 "
                                             f"등록하실 수 있습니다.\n[봇에 하트 누르러 가기]"
                                             f"(https://koreanbots.dev/bots/790968269007880232)")
        tags_list.append(tag)
        new_tags = ','.join(tags_list)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        data = [(ctx.guild.id, self.key.encrypt(new_tags))]
        cursor.execute(f'DELETE FROM banned_tags WHERE guild = "{ctx.guild.id}"')
        cursor.executemany("INSERT INTO banned_tags(guild, tags) VALUES(?,?)", data)
        conn.commit()
        conn.close()
        embed = discord.Embed(description=f'`{tag}` 태그를 금지 태그에 추가했습니다.', color=0x00c062)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        return await ctx.send(ctx.author.mention, embed=embed)

    @_tag.command(name='삭제', aliases=['delete', 'd'])
    async def delete(self, ctx, *, tag=None):
        tags = await self.get_tags(ctx, tag)
        if type(tags) != str:
            return None

        tag = tag.lower().replace(' ', '').replace('female:', '') \
            .replace('male:', '').replace('여:', '').replace('남:', '')
        if tag not in tags:
            return await send(self.bot, ctx, "등록되지 않은 태그입니다.")

        tags_list = [t for t in tags.split(',')]
        new_tags = []
        for t in tags_list:
            if tag == t:
                continue
            new_tags.append(t)
        new_tags = ','.join(new_tags)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        data = [(ctx.guild.id, self.key.encrypt(new_tags))]
        cursor.execute(f'DELETE FROM banned_tags WHERE guild = "{ctx.guild.id}"')
        cursor.executemany("INSERT INTO banned_tags(guild, tags) VALUES(?,?)", data)
        conn.commit()
        conn.close()
        embed = discord.Embed(description=f'`{tag}` 태그를 금지 태그에서 삭제했습니다.', color=0x00c062)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        return await ctx.send(ctx.author.mention, embed=embed)


def setup(bot):
    bot.add_cog(Tags(bot))

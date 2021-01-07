import sqlite3
import asyncio
import discord
import koreanbots
from discord.ext import commands, tasks
from discord.errors import NotFound
from modules.util import send, cleanup, config, determine_prefix


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = koreanbots.Client(self.bot, config()['kbl_token'])
        self.lookup.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print('=' * 40)
        print(f'{self.bot.user.name}(으)로 로그인합니다.')
        print(f'접속 중인 서버: {len(self.bot.guilds)}개')
        print('=' * 40)
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.playing, name=f'/도움말'))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        user = cursor.execute(f'SELECT * FROM user WHERE user = "{ctx.author.id}"').fetchone()

        if not user:
            is_voted = await self.client.getVote(ctx.author.id)
            if is_voted.voted is True:
                data = [(ctx.author.id, 'voter')]
                cursor.executemany("INSERT INTO user(user, rank) VALUES(?,?)", data)
                conn.commit()
                return conn.close()

    @tasks.loop(seconds=600)
    async def lookup(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                users = cursor.execute(f'SELECT * FROM user WHERE rank = "voter"').fetchall()
                bot_votes = await self.client.getVote(790968269007880232)

                if len(users) == bot_votes.votes:
                    pass
                else:
                    for u in users:
                        vote = await self.client.getVote(u[0])
                        if vote.voted is True:
                            pass
                        else:
                            cursor.execute(f'DELETE FROM user WHERE user = "{u[0]}"')
                            conn.commit()
            except:
                pass
            await asyncio.sleep(600)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return None
        if isinstance(error, NotFound):
            return None
        elif isinstance(error, commands.CommandOnCooldown):
            description = f"이 명령어는 {int(error.retry_after)}초 후에 다시 사용할 수 있습니다.\n" \
                          f"봇에 하트를 눌러주시면 쿨타임이 20초로 감소합니다.\n" \
                          f"[봇에 하트 누르러 가기](https://koreanbots.dev/bots/790968269007880232)"
            return await send(self.bot, ctx, description)
        elif "403 Forbidden (error code: 50013)" in str(error):
            try:
                return await send(self.bot, ctx, "봇에 할당된 권한이 부족합니다.")
            except:
                try:
                    return await ctx.send("봇에 할당된 권한이 부족합니다.")
                except:
                    return None
        else:
            description = f"알 수 없는 에러가 발생하였습니다. " \
                          f"다음 에러 내용을 [지원 서버](https://discord.gg/{config()['support']})" \
                          f"에 제보해주세요.```" \
                          f"\nError occurred while using {ctx.message.content}\n{error}```"
            return await send(self.bot, ctx, description)

    @commands.command(name='접두사', aliases=['prefix'],
                      usage="", description="접두사를 설정합니다.")
    async def prefix(self, ctx):
        def check(m):
            if m.author != ctx.author or m.channel != ctx.channel:
                return None
            try:
                content = int(m.content)
            except ValueError:
                return None
            if 3 > content:
                return m.author == ctx.author and m.channel == ctx.channel

        if not ctx.author.guild_permissions.manage_channels and ctx.author != discord.AppInfo.owner:
            return await send(self.bot, ctx, "당신은 이 명령어를 사용할 권한이 없습니다.")

        embed = discord.Embed(title='모드를 선택하세요.', color=0x00c062,
                              description=f"1. 접두사 초기화(`{config()['prefix']}`)\n"
                                          f"2. 사용자 지정 접두사 설정")
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        msg = await ctx.send(ctx.author.mention, embed=embed)

        try:
            respond = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await cleanup(msg)

        await cleanup(msg, respond)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        if int(respond.content) == 1:
            cursor.execute(f'DELETE FROM prefix WHERE guild = "{ctx.guild.id}"')
            conn.commit()
            conn.close()
            embed = discord.Embed(description=f'접두사가 초기화되었습니다.'
                                              f' 현재 접두사는 `{config()["prefix"]}`입니다.',
                                  color=0x00c062)
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
            return await ctx.send(ctx.author.mention, embed=embed)

        else:
            embed = discord.Embed(title='설정할 접두사를 입력하세요.', color=0x00c062)
            embed.add_field(name='주의사항',
                            value='설정할 접두사 그대로 채팅창에 입력하세요. (명령어가 아닙니다.)\n'
                                  '접두사가 띄어쓰기를 포함하는 경우, 반드시 띄어쓰기 대신 `{공백}`으로 입력해주세요.\n'
                                  '예시) `아쿠아 ` ⇒ `아쿠아{공백}`')
            embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
            msg = await ctx.send(ctx.author.mention, embed=embed)
            try:
                respond = await self.bot.wait_for('message', timeout=60,
                                                  check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except asyncio.TimeoutError:
                conn.close()
                return await cleanup(msg)

            prefix = respond.content.replace(' ', '').replace('{공백}', ' ')
            cursor.execute(f'DELETE FROM prefix WHERE guild = {ctx.guild.id}')
            data = [(ctx.guild.id, prefix)]
            cursor.executemany(f'INSERT INTO prefix(guild, prefix) VALUES(?,?)', data)
            conn.commit()
            conn.close()
            await cleanup(msg, respond)

            embed = discord.Embed(description=f'접두사가 설정되었습니다. 현재 접두사는 `{prefix}`입니다.')
            return await ctx.send(ctx.author.mention, embed=embed)

    @commands.command(name='도움말', aliases=['help'],
                      usage="", description="이 메시지를 한 번 더 확인합니다.")
    async def help(self, ctx):
        embed = discord.Embed(title=f"{self.bot.user.name} 도움말", color=0x45c9e9)
        for c in self.bot.commands:
            if c.hidden is True:
                continue
            embed.add_field(name=f"{await determine_prefix(self.bot, ctx)}{c.name} {c.usage}",
                            value=c.description, inline=False)
        embed.add_field(name=f"{config()['prefix']}초기화",
                        value="접두사를 초기화합니다.", inline=False)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return await ctx.send(ctx.author.mention, embed=embed)


def setup(bot):
    bot.add_cog(Event(bot))

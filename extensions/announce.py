import discord
from discord.ext import commands
from modules.util import config


class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != discord.AppInfo.owner and \
                str(message.channel.id) != config()['announce_channel']:
            return None

        content = f"\n\n공지 채널이 설정되지 않았거나 권한이 부족한 경우, 무작위 채널로 공지가 전송될 수 있습니다." \
                  f"\n이 경우, 채널 이름에 `공지` 단어를 추가해주시기 바랍니다." \
                  f"\n[Aquahegao-Bot 지원서버](https://discord.gg/{config()['support']})"

        contents = message.content.split('\n')
        if contents[0].startswith('**'):
            title = contents[0]
            description = '\n'.join(contents[1:])
        else:
            title = ''
            description = message.content

        embed = discord.Embed(title=title, description=description + content, color=0xa1e970)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        for guild in self.bot.guilds:
            is_ac = False
            for channel in guild.channels:
                if '공지' in channel.name:
                    try:
                        await channel.send(embed=embed)
                        is_ac = True
                        break
                    except:
                        pass

            if is_ac is True or guild.id == 792966225743183872:
                continue

            for channel in guild.channels:
                try:
                    await channel.send(embed=embed)
                    break
                except:
                    pass


def setup(bot):
    bot.add_cog(Announce(bot))

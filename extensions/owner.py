import ast
import asyncio
import discord
from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def eval(self, ctx, *, cmd=None):
        if ctx.author.id != 244070533241634816 or not cmd:
            return None

        async def insert_returns(b):
            if isinstance(b[-1], ast.Expr):
                b[-1] = ast.Return(b[-1].value)
                ast.fix_missing_locations(b[-1])
            if isinstance(b[-1], ast.If):
                insert_returns(b[-1].b)
                insert_returns(b[-1].orelse)
            if isinstance(b[-1], ast.With):
                insert_returns(b[-1].b)

        try:
            fn_name = "_eval_expr"
            cmd = cmd.strip("` ")
            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
            body = f"async def {fn_name}():\n{cmd}"
            parsed = ast.parse(body)
            body = parsed.body[0].body
            await insert_returns(body)
            env = {
                'bot': ctx.bot,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                '__import__': __import__
            }
            exec(compile(parsed, filename="<ast>", mode="exec"), env)
            result = (await eval(f"{fn_name}()", env))
            embed = discord.Embed(title='정상적으로 처리되었습니다.', description=f'```{str(result)}```', color=0x00c062)
            embed_success = discord.Embed(description='정상적으로 처리되었습니다.', color=0x00c062)
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            try:
                return await msg.edit(embed=embed_success)
            except:
                return
        except Exception as e:
            embed = discord.Embed(title='처리할 수 없습니다.', description=f'```{e}```', color=0xFF0000)
            return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Owner(bot))

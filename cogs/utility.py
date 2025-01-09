import discord
from discord.ext import commands

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def ping(self, ctx):
        await ctx.reply(f'pong {round(self.bot.latency*1000)}ms')
    
    @commands.command()
    async def wait(self,ctx,time: int):
        await asyncio.sleep(time)
        await ctx.reply(f"Waited {time} seconds")

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
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

    @commands.command()
    async def icon(self,ctx, member: discord.Member):
        await ctx.reply(member.avatar)

    @commands.command()
    async def playing(self,ctx, *args):
        activity = discord.Game(name=' '.join(args))
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
import asyncio
from pathlib import Path

import discord
from discord.ext import commands


class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def ping(self, ctx):
        await ctx.reply(f"pong {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def wait(self, ctx, time: int):
        await asyncio.sleep(time)
        await ctx.reply(f"Waited {time} seconds")

    @commands.command()
    async def icon(self, ctx, member: discord.Member):
        await ctx.reply(member.avatar)

    @commands.command()
    async def facepalm(self, ctx):
        await ctx.message.edit(content="(－‸ლ)")

    @commands.command()
    async def playing(self, ctx, *args):
        activity = discord.Game(name=" ".join(args))
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        await ctx.message.delete()

    @commands.command()
    async def everyone(self, ctx):
        buffer = ""
        for member in ctx.message.guild.members:
            buffer = buffer + member.mention

        await ctx.message.edit(buffer)

    @commands.command()
    async def allchannelsend(self, ctx, content):
        for channel in ctx.message.guild.text_channels:
            try:
                await channel.send(content)
            except discord.Forbidden:
                pass

    @commands.command()
    async def version(self, ctx):
        version_file = Path("./version.txt")
        await ctx.reply(f"Version: {version_file.read_text()}")


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))

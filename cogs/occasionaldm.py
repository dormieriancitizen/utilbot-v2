import random
import asyncio
from discord.ext import commands


class OcassionalMessager(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def occasional_message(self, ctx, count: int = 10, max_minutes: int = 20):
        messages = [
            "darn",
            "drats",
            "goshdarnit",
            "oops",
            "curses",
            "argh",
            "heck",
            "dang",
            "golly",
            "balderdash",
            "holy cow",
            "dangnabbit",
            "shoot",
            "gee",
        ]
        for i in range(count):
            await asyncio.sleep(random.randrange(60, max_minutes * 60))
            await ctx.channel.send(random.choice(messages))


async def setup(bot):
    await bot.add_cog(OcassionalMessager(bot))

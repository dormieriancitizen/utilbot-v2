import discord
from discord.ext import commands

class MessagesCommands(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        
    async def _spam(self,channel,string,count):
        if len(string) > 2000:
            raise Exception("String must be shorter than 2000 characters")

        for i in range(count):
            await channel.send(string)

    @commands.command()
    async def spam(self,ctx,count: int,*args):
        await ctx.message.delete()
        await _spam(ctx.channel," ".join(args), count)

    @commands.command()
    async def lag(self,ctx,count: int,channel=None):
        if channel is None:
            channel = ctx.channel
        else:
            channel = await discord.get_channel(channel)

        await _spam(channel,398*"🅰",count)
    
    @commands.command()
    async def whitespace(self,ctx):
        await ctx.channel.send("‫"+"\n"*1998+"‫")
        await ctx.message.delete()

    @commands.command()
    async def spoil(self,ctx, *args):
        spoiled = "".join([f"||{x}||" for x in regex.findall(r'(.)'," ".join(args))])

        await ctx.message.edit(spoiled)

    @commands.command()
    async def nuke(self, ctx, count: int):
        messages = [message async for message in ctx.channel.history(limit=count)]
        for message in messages:
            await message.delete()

async def setup(bot):
    await bot.add_cog(MessagesCommands(bot))
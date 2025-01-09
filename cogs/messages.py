import discord
from discord.ext import commands

from colorama import Fore, Back, Style

colorama_replacements = {
    # Foreground colors
    r"{Fore.Green}": Fore.GREEN,
    r"{Fore.Blue}": Fore.BLUE,
    r"{Fore.Red}": Fore.RED,
    r"{Fore.Yellow}": Fore.YELLOW,
    r"{Fore.Cyan}": Fore.CYAN,
    r"{Fore.White}": Fore.WHITE,
    r"{Fore.Magenta}": Fore.MAGENTA,
    r"{Fore.Reset}": Fore.RESET,
    
    # Background colors
    r"{Back.Green}": Back.GREEN,
    r"{Back.Blue}": Back.BLUE,
    r"{Back.Red}": Back.RED,
    r"{Back.Yellow}": Back.YELLOW,
    r"{Back.Cyan}": Back.CYAN,
    r"{Back.White}": Back.WHITE,
    r"{Back.Magenta}": Back.MAGENTA,
    r"{Back.Reset}": Back.RESET,
    
    # Styles
    r"{Style.Bright}": Style.BRIGHT,
    r"{Style.Dim}": Style.DIM,
    r"{Style.Normal}": Style.NORMAL,
    r"{Style.Reset}": Style.RESET_ALL,
}

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

    @commands.command(name="colorama")
    async def colorama_message(self,ctx,*args):
        colored = " ".join(args)
        for match, color in colorama_replacements.items():
            colored = colored.replace(match,color)
        
        await ctx.message.edit(f"```ansi\n{colored}```")

async def setup(bot):
    await bot.add_cog(MessagesCommands(bot))
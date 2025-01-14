import discord
from discord.ext import commands

class MimicCommands(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def mimic(self,ctx,target: discord.Member,*args):
        message = " ".join(args)

        wooks = await ctx.channel.webhooks()

        created_webhook = False
        if wooks:
            webhook = wooks[0]
        else:
            webhook = await ctx.channel.create_webhook(name="empheral",reason="Empheral webhook")
            created_webhook = True

        await ctx.message.delete()

        await webhook.send(
            content=message,
            avatar_url=target.avatar,
            username=target.display_name
        )

        if created_webhook:
            await webhook.delete(reason="Empheral webhook for mimicry")

async def setup(bot):
    await bot.add_cog(MimicCommands(bot))
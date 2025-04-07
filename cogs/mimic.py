import discord
from discord.ext import commands

class MimicCommands(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def _sayas(self, channel, avatar_url, username, message):
        if isinstance(channel,discord.TextChannel):
            webhooks = await channel.webhooks()

            created_webhook = False
            if webhooks:
                webhook = webhooks[0]
            else:
                webhook = await channel.create_webhook(name="ephemeral",reason="ephemeral webhook")
                created_webhook = True
        else:
            return

        await webhook.send(
            content=message,
            avatar_url=avatar_url,
            username=username
        )

        if created_webhook:
            await webhook.delete(reason="Empheral webhook for mimicry")

    @commands.command()
    async def mimic(self, ctx, target: discord.Member,*args):
        message = " ".join(args)
        await ctx.message.delete()

        await self._sayas(ctx.channel, target.avatar, target.display_name, message)

    @commands.command()
    async def persona(self, ctx, avatar_url: str, username: str, message: str):
        await ctx.message.delete()

        await self._sayas(ctx.channel, avatar_url, username, message)

async def setup(bot):
    await bot.add_cog(MimicCommands(bot))

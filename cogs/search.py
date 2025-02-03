import discord
from discord.ext import commands

class SearchCommands(commands.Cog):
    """Commands to deal with the searching of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    def sort_dict(self,x):
        return dict(sorted(x.items(), key=lambda item: item[1]))

    @commands.group()
    async def count(self,ctx):
        if ctx.subcommand_passed is None:
            m = await ctx.reply("Loading...")

            message: discord.Message = [m async for m in ctx.guild.search(limit=1)][0]
            await m.edit(f"{message.total_results} messages")
        elif ctx.invoked_subcommand is None:
            await ctx.reply(f"Searchtype {ctx.subcommand_passed} does not exist")

    @count.command(name="user")
    async def user_count(self,ctx,*args):
        search_string = " ".join(args)
        m = await ctx.reply("Loading...")

        counts = {}

        members = await ctx.guild.fetch_members()

        initial_search = [m async for m in ctx.guild.search(
                content=search_string,
                limit=1)]

        if not initial_search:
            total: int = 0
        else:
            total = initial_search[0].total_results

        if total > len(members) * 25:
            for member in members:
                messages = [m async for m in ctx.guild.search(
                    content=search_string,
                    authors=[member],
                    limit=1)]
                if messages:
                    message_count = messages[0].total_results
                else:
                    message_count = 0

                counts[member.name] = message_count
        else:
            # More efficient to go through a raw search
            if total > 0:
                async for message in ctx.guild.search(content=search_string,limit=None):
                    if message.author in counts:
                        counts[message.author] += 1
                    else:
                        counts[message.author] = 1

            for member in members:
                if member not in counts:
                    counts[member] = 0


        counts=self.sort_dict(counts)

        response = "# "+f"{search_string}: {total}\n" if search_string else 'Users\n'
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        print(response)
        await m.edit(response)

    @count.command(name="imager")
    async def image_count(self,ctx):
        m = await ctx.reply("Loading...")

        counts = {}
        for member in (await ctx.guild.fetch_members()):
            messages = [m async for m in ctx.guild.search(
                has=["image"],
                authors=[member],
                limit=1)]
            if messages:
                message_count = messages[0].total_results
            else:
                message_count = 0

            counts[member.name] = message_count

        counts=self.sort_dict(counts)

        response = f"# {'Imagers'}\n"
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        print(response)
        await m.edit(response)

    @count.command(name="message_per_capita")
    async def per_capita_count(self,ctx,*args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        counts = {}
        for member in (await ctx.guild.fetch_members()):
            content_messages = [m async for m in ctx.guild.search(
                content=search_string,
                authors=[member],
                limit=1)]
            
            if content_messages:
                content_message_count = content_messages[0].total_results

                max_messages = [m async for m in ctx.guild.search(
                    authors=[member],
                    limit=1)]

                max_messages_count = max_messages[0].total_results

                message_percent = (content_message_count / max_messages_count)
            else:
                message_percent = 0

            counts[member] = message_percent

        counts=self.sort_dict(counts)

        response = f"# {f'{search_string} per capita' if search_string else 'Message Per Capita'}\n"
        response += "\n".join([f"-`{member}`: `{counts[member]*100}%`" for member in counts])
        
        print(response)
        
        await m.edit(response)

    @count.command(name="mentions")
    async def mentions_count(self,ctx,*args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        counts = {}
        for member in (await ctx.guild.fetch_members()):
            messages = [m async for m in ctx.guild.search(
                content=search_string,
                mentions=[member],
                limit=1)]
            if messages:
                message_count = messages[0].total_results
            else:
                message_count = 0

            counts[member.name] = message_count

        counts=self.sort_dict(counts)

        response = f"# {search_string if search_string else 'Users'}\n"
        response += "\n".join([f"-`{member}` has been mentioned `{counts[member]}` times" for member in counts])
        print(response)
        await m.edit(response)
    
    @count.command(name="channel")
    async def channels_count(self,ctx,*args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        counts = {}
        for channel in ctx.guild.text_channels:
            messages = [m async for m in channel.search(
                content=search_string,
                limit=1)]
            if messages:
                message_count = messages[0].total_results
            else:
                message_count = 0

            counts[channel] = message_count

        counts=self.sort_dict(counts)

        response = f"# {search_string if search_string else 'Channels'}\n"
        response += "\n".join([f"-`{channel}` has {counts[channel]} messages" for channel in counts])
        print(response)
        await m.edit(response)
        return

async def setup(bot):
    await bot.add_cog(SearchCommands(bot))    

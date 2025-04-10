from typing import Any, Callable, Iterable
import discord
from discord.ext import commands

class SearchCommands(commands.Cog):
    """Commands to deal with the searching of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    def sort_dict(self,x):
        return dict(sorted(x.items(), key=lambda item: item[1]))

    def slice_string(self, s, size=2000):
        return [s[i:i+size] for i in range(0, len(s), size)]

    async def _get_counts(
        self,
        guild: discord.Guild,
        search_string: str,
        entities: list[Any],
        message_transformer: Callable[[discord.Message],Any],
        search_arg: str | None = None,
        no_raw: bool = False,
        extra_args: dict[str,Any] = {},
    ) -> tuple[dict[Any,int],int]:
        initial_search = [m async for m in guild.search(
                content=search_string,
                **extra_args,
                limit=1)]

        counts: dict[Any,int] = {}

        if not initial_search:
            total: int = 0
        else:
            total = initial_search[0].total_results # type: ignore

        if (total > len(entities) * 25) or no_raw:
            for entity in entities:
                if search_arg:
                    search = guild.search(
                        content=search_string,
                        limit=1,
                        **{search_arg: [entity]}, 
                        **extra_args
                    )
                else:
                    search = guild.search(
                        content=search_string,
                        limit=1,
                        **extra_args
                    )

                try:
                    messages = [m async for m in search]
                    
                    if messages:
                        message_count: int = messages[0].total_results # type: ignore
                    else:
                        message_count = 0

                    if message_count:
                        counts[entity] = message_count
                except discord.errors.Forbidden:
                    counts[entity] = -1
        else:
            # More efficient to go through a raw search
            if total > 0:
                async for message in guild.search(content=search_string,limit=None):
                    entity = message_transformer(message)
                    
                    if entity in counts:
                        counts[entity] += 1
                    else:
                        counts[entity] = 1

            # for entity in entities:
                # if entity not in counts:
                    # counts[entity] = 0

        counts=self.sort_dict(counts)
        return counts, total

    @commands.group()
    async def count(self,ctx):
        if ctx.subcommand_passed is None:
            m = await ctx.reply("Loading...")

            message: discord.Message = [m async for m in ctx.channel.search(limit=1)][0]
            await m.edit(f"{message.total_results} messages")
        elif ctx.invoked_subcommand is None:
            await ctx.reply(f"Searchtype {ctx.subcommand_passed} does not exist")

    @count.command(name="users")
    async def user_count(self,ctx,*args):
        search_string = " ".join(args)
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            search_arg="authors",
        )

        response = "# "+f"{search_string}: {total}\n" if search_string else 'Users\n'
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        
        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)
    
    @count.command(name="compare")
    async def comparison_count(self,ctx,*queries):
        m = await ctx.reply("Loading...")

        counts = {} 
        for query in queries:
            search: list[discord.Message] = [m async for m in ctx.guild.search(
                content=query,
                limit=1)]

            if search:
                counts[query] = search[0].total_results
            else:
                counts[query] = 0

        response = "# Comparisons \n"
        response += "\n".join([f"-`{query}`: `{counts[query]}` messages" for query in counts])

        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)

    @count.command(name="users_in_channel")
    async def channel_user_count(self,ctx,channel: discord.TextChannel):
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string="",
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            search_arg="authors",
            extra_args={"channels": [channel]}
        )

        response = "# "+f"{channel.name}: {total}\n"
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        
        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)

    @count.command(name="imagers")
    async def image_count(self,ctx):
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string="",
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            search_arg="authors",
            extra_args={"has": ["image"]}
        )

        response = f"# Images: {total}\n"
        response += "\n".join([f"-`{member.name}` has sent `{counts[member]}` images" for member in counts])
        
        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)

    @count.command(name="messages_per_capita")
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
                
        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)

    @count.command(name="mentions")
    async def mentions_count(self,ctx):
        m = await ctx.reply("Loading...")
        search_string = ""

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: None,
            search_arg="mentions",
            no_raw=True
        )

        response = f"# Mentions\n"
        response += "\n".join([f"-`{member.name}` has been mentioned `{counts[member]}` times" for member in counts])

        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)
    
    @count.command(name="channels")
    async def channels_count(self,ctx,*args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=ctx.guild.text_channels,
            message_transformer=lambda message: message.channel,
            search_arg="channels",
        )

        response = f"# {search_string}: {total}\n" if search_string else '# Channels\n'
        response += "\n".join([f"-`{channel.name}` has {counts[channel]} messages" for channel in counts])

        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)
                

async def setup(bot):
    await bot.add_cog(SearchCommands(bot))    

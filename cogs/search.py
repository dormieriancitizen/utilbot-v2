from typing import Any, Callable, TypeVar
import discord
import json
import asyncio
from pathlib import Path
from datetime import datetime
from discord.ext import commands

T = TypeVar("T")

class SearchCommands(commands.Cog):
    """Commands to deal with the searching of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    def sort_dict(self,x) -> dict[Any,Any]:
        return dict(sorted(x.items(), key=lambda item: item[1]))

    def slice_string(self, s, size=2000):
        return [s[i:i+size] for i in range(0, len(s), size)]

    async def _get_counts(
        self,
        guild: discord.Guild,
        entities: list[T],
        message_transformer: Callable[[discord.Message], T] | None,
        name_transformer: Callable[[T], str],
        search_string: str = "",
        search_arg: str | None = None,
        extra_args: dict[str, Any] = {},
    ) -> tuple[dict[tuple[str,T | None],int], int]:
        initial_search = [m async for m in guild.search(
                content=search_string,
                **extra_args,
                limit=1)]

        counts: dict[Any, int] = {}

        if not initial_search:
            total: int = 0
        else:
            total = initial_search[0].total_results # type: ignore
        
        remaining: int = total

        if (total > len(entities) * 25) or (message_transformer is None):
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

                    entity_name = name_transformer(entity)

                    counts[(entity_name, entity)] = message_count
                    remaining -= message_count
                except discord.errors.Forbidden:
                    counts[(entity_name, entity)] = -1
        else:
            # More efficient to go through a raw search
            if total > 0:
                async for message in guild.search(content=search_string,limit=None):
                    entity = message_transformer(message)
                    entity_name = name_transformer(entity)

                    if entity not in counts:
                        counts[(entity_name, entity)] = 0
                    
                    counts[(entity_name, entity)] += 1
                    remaining -= 1

        if remaining:
            counts[("other", None)] = remaining
        
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
    
    @count.command(name="build_cache")
    async def build_cache(self,ctx):
        def check(m: discord.Message):
            if m.channel.id != ctx.channel.id:
                return False

            if m.author.id != ctx.message.author.id:
                return False

            if m.content.lower() in ["y","yes","yeah","yea","yay"]:
                return True

            raise asyncio.TimeoutError

        if not ctx.guild:
            await ctx.reply("This command can't be run outside a guild!")
            return

        cache_path = Path(f"cache/message_count_cache.{ctx.guild.id}")
        if cache_path.exists():
            last_cache_str = datetime.fromtimestamp(cache_path.lstat().st_mtime).strftime("%m/%d/%Y")
            await ctx.reply(f"Last cache was {last_cache_str}. Continue? Y/n")

            try:
                await self.bot.wait_for('message', check = check, timeout = 60.0)
            except asyncio.TimeoutError:
                await ctx.reply("Not contiuing")
                return

            await ctx.reply('Continuing')

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda user: user.name,
            search_arg="authors",
        )

        id_counts: dict[int, int] = {member[1].id: count for member, count in counts.items() if not (member[1] is None)}

        with open(cache_path,"w") as cache_file:
            json.dump(id_counts, cache_file)
        
        await ctx.reply(f"Built cache of {len(id_counts)} members")
    

    @count.command(name="users")
    async def user_count(self,ctx,*args):
        search_string = " ".join(args)
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
        )

        response = f" # {search_string}: {total}\n"
        response += "\n".join([f" - `{member[0]}` has sent `{counts[member]}` messages" for member in counts])
        
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
        response += "\n".join([f" - `{query}`: `{counts[query]}` messages" for query in counts])

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
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
            extra_args={"has": ["image"]}
        )

    
        response = f"# Images: {total}\n"
        response += "\n".join([f" - `{member[0]}` has sent `{counts[member]}` images" for member in counts])
        
        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)

    @count.command(name="per_capita")
    async def per_capita_count(self,ctx,*args):
        def round_to_sig_figs(number,figs=3):
            return '{:g}'.format(float('{:.{p}g}'.format(number,p=figs)))
    
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        cache_path = Path(f"cache/message_count_cache.{ctx.guild.id}")
        if not cache_path.exists():
            await ctx.reply("No cache found! Build the cache with `build_cache` and try again")
            return
        
        with open(cache_path, "r") as cache_file:
            total_counts = json.load(cache_file)
        # await ctx.reply(f"Counts: {total_counts}")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
        )

        rates: dict[tuple[str, discord.User | discord.Member],int] = {}
        for member, count in counts.items():
            if member[1] is None:
                continue
            if str(member[1].id) in total_counts:
                rates[(member[0], member[1])] = count / total_counts[str(member[1].id)]

        rates = self.sort_dict(rates)

        response = f"# {search_string} per capita\n"
        response += "\n".join([f" - `{member[0]}`: **{round_to_sig_figs(rates[member]*100,4)}%**  ->  {counts[member]}" for member in rates])
                
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
            message_transformer=None,
            name_transformer=lambda author: author.name,
            search_arg="mentions",
        )

        response = f"# Mentions: {total}\n"
        response += "\n".join([f" - `{member[0]}` has been mentioned `{counts[member]}` times" for member in counts])

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
            name_transformer=lambda channel: channel.name if isinstance(channel,discord.TextChannel) else "Unknown Channel",
            search_arg="channels",
        )

        response = f"# {search_string}: {total}\n" if search_string else '# Channels\n'
        response += "\n".join([f" - `{channel[0]}` has {counts[channel]} messages" for channel in counts])

        if len(response) < 2000:
            await m.edit(response)
        else:
            responses = self.slice_string(response)
            
            for response in responses:
                await m.channel.send(response)
                

async def setup(bot):
    await bot.add_cog(SearchCommands(bot))    

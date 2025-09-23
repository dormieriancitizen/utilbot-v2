from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Mapping, TypeVar

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from discord import Guild, Member, Message, User
    from discord.abc import MessageableChannel

T = TypeVar("T")

CACHE_ROOT = Path("./cache")


class SearchCommands(commands.Cog):
    """Commands to deal with the searching of messages"""

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    def sort_dict(self, x: dict[T, Any]) -> dict[T, Any]:
        return dict(sorted(x.items(), key=lambda item: item[1]))

    def count_status_update(self, message):
        last_completed = 0

        async def update(completed: int, total: int):
            nonlocal last_completed

            if (total / 5) > 100:
                step = total / 5
            else:
                step = 100

            if completed - last_completed > step or completed == total:
                last_completed = completed
                await message.edit(content=f"Loading... {completed} / {total}")

        return update

    async def _get_counts(
        self,
        guild: Guild,
        entities: list[T],
        message_transformer: Callable[[Message], T] | None,
        name_transformer: Callable[[T], str],
        status_update: Callable[[int, int], Awaitable[None]] | None,
        search_string: str = "",
        search_arg: str | None = None,
        extra_args: dict[str, Any] = {},
    ) -> tuple[dict[tuple[str, T | None], int], int]:
        initial_search = [
            m async for m in guild.search(content=search_string, **extra_args, limit=1)
        ]

        counts: dict[tuple[str, T | None], int] = {}

        if not initial_search:
            total: int = 0
        else:
            total = initial_search[0].total_results  # type: ignore

        remaining: int = total

        if (total > len(entities) * 25) or (message_transformer is None):
            for entity in entities:
                if search_arg:
                    search = guild.search(
                        content=search_string,
                        limit=1,
                        **{search_arg: [entity]},
                        **extra_args,
                    )
                else:
                    search = guild.search(content=search_string, limit=1, **extra_args)

                entity_name = name_transformer(entity)

                try:
                    messages = [m async for m in search]
                except discord.Forbidden:
                    counts[(entity_name, entity)] = -1
                    continue

                if messages:
                    message_count: int = messages[0].total_results  # type: ignore
                else:
                    message_count = 0

                counts[(entity_name, entity)] = message_count
                remaining -= message_count

                if status_update:
                    await status_update(total - remaining, total)

                if remaining == 0:
                    break
        else:
            # More efficient to go through a raw search
            if total > 0:
                async for message in guild.search(content=search_string, limit=None):
                    entity = message_transformer(message)
                    entity_name = name_transformer(entity)

                    entity_key = (entity_name, entity)

                    if entity_key not in counts:
                        counts[entity_key] = 0

                    counts[entity_key] += 1
                    remaining -= 1

                    if status_update:
                        await status_update(total - remaining, total)

        if remaining:
            counts[("other", None)] = remaining

        if status_update:
            await status_update(total, total)

        counts = self.sort_dict(counts)
        return counts, total

    async def _respond(self, message: Message, response: str):
        if len(response) < 2000:
            await message.edit(content=response)
        else:
            chunks: list[str] = []
            curr_chunk: str = ""
            for line in response.splitlines(keepends=True):
                if len(line) + len(curr_chunk) < 2000:
                    curr_chunk += line
                else:
                    chunks.append(curr_chunk)
                    curr_chunk = line
            chunks.append(curr_chunk)

            for chunk in chunks:
                await message.channel.send(chunk)

            await message.edit(content="Done")

    def _store_guild_channel_counts(
        self,
        guild: Guild,
        counts: Mapping[tuple[str, MessageableChannel | None], int],
    ):
        cache_path = CACHE_ROOT / f"channel_count_cache.{guild.id}"
        id_counts: dict[int, int] = {
            channel[1].id: count
            for channel, count in counts.items()
            if channel[1] is not None
        }

        with open(cache_path, "w") as cache_file:
            json.dump(id_counts, cache_file)

    def _get_guild_channel_count_cache(self, guild: Guild) -> dict[str, int] | None:
        cache_path = CACHE_ROOT / f"channel_count_cache.{guild.id}"
        if not cache_path.exists():
            return None

        with open(cache_path, "r") as cache_file:
            total_counts = json.load(cache_file)

        return total_counts

    def _store_guild_message_counts(
        self,
        guild: Guild,
        counts: Mapping[tuple[str, User | Member | None], int],
    ):
        cache_path = CACHE_ROOT / f"message_count_cache.{guild.id}"
        id_counts: dict[int, int] = {
            member[1].id: count
            for member, count in counts.items()
            if member[1] is not None
        }

        with open(cache_path, "w") as cache_file:
            json.dump(id_counts, cache_file)

    def _get_message_count_cache(self, guild: Guild) -> dict[str, int] | None:
        cache_path = CACHE_ROOT / f"message_count_cache.{guild.id}"
        if not cache_path.exists():
            return None

        with open(cache_path, "r") as cache_file:
            total_counts = json.load(cache_file)

        return total_counts

    @commands.group(name="count")
    async def count(self, ctx):
        pass

    @count.command(name="build_cache")
    async def build_cache(self, ctx):
        def check(m: Message):
            if m.channel.id != ctx.channel.id:
                return False

            if m.author.id != ctx.message.author.id:
                return False

            if m.content.lower() in ["y", "yes", "yeah", "yea", "yay"]:
                return True

            raise asyncio.TimeoutError

        if not ctx.guild:
            await ctx.reply("This command can't be run outside a guild!")
            return

        cache_path = CACHE_ROOT / f"message_count_cache.{ctx.guild.id}"
        if cache_path.exists():
            last_cache_str = datetime.fromtimestamp(
                cache_path.lstat().st_mtime
            ).strftime("%m/%d/%Y")
            await ctx.reply(f"Last cache was {last_cache_str}. Continue? Y/n")

            try:
                await self.bot.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.reply("Not contiuing")
                return

            await ctx.reply("Continuing")

        counts, _ = await self._get_counts(
            guild=ctx.message.guild,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda user: user.name,
            search_arg="authors",
            status_update=None,
        )

        self._store_guild_message_counts(ctx.guild, counts)
        await ctx.reply(
            f"Built cache of {len([count for count in counts if count is not None])} members"
        )

    @count.command(name="users")
    async def user_count(self, ctx, *args):
        search_string = " ".join(args)
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
            status_update=self.count_status_update(m),
        )

        if not search_string:
            self._store_guild_message_counts(ctx.guild, counts)

        response = f" # {search_string}: {total}\n"
        response += "\n".join(
            [
                f" - `{member[0]}` has sent `{counts[member]}` messages"
                for member in counts
            ]
        )

        await self._respond(m, response)

    @count.command(name="pings")
    async def ping_count(self, ctx, target: discord.Member):
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=f"<@{target.id}>",
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
            status_update=self.count_status_update(m),
        )

        response = f" # Pings for {target.name}: {total}\n"
        response += "\n".join(
            [
                f" - `{member[0]}` has pinged them `{counts[member]}` times"
                for member in counts
            ]
        )

        await self._respond(m, response)

    @count.command(name="per_cent")
    async def per_cent(self, ctx, *queries):
        m = await ctx.reply("Loading...")
        search: list[Message] = [
            m
            async for m in ctx.guild.search(
                before=datetime.combine(date.today() + timedelta(days=1), time.min),
                limit=1,
            )
        ]

        total_counts = self._get_message_count_cache(ctx.guild)
        if not total_counts:
            await ctx.reply(
                "No cache found! Build the cache with `build_cache` and try again"
            )
            return

        members = {str(m.id): m for m in await ctx.guild.fetch_members()}

        if search and search[0].total_results:
            total_messages = search[0].total_results
        else:
            total_messages = 0

        response = "# percent \n"
        response += "\n".join(
            f" - `{members[member_id].name}`: "
            + f"`{self.round_to_sig_figs((count / total_messages) * 100)}%`"
            for member_id, count in total_counts.items()
        )

        await self._respond(m, response)

    @count.command(name="cached_channels")
    async def cached_channels(
        self,
        ctx,
    ):
        m = await ctx.reply("Loading...")
        total_counts = self._get_guild_channel_count_cache(ctx.guild)
        if not total_counts:
            await ctx.reply(
                "No cache found! Build the cache with `build_cache` and try again"
            )
            return

        channels = {x: self.bot.get_channel(int(x)).name for x in total_counts.keys()}

        response = "# Channels \n"
        response += "\n".join(
            f" - `{channels[channel_id]}`: `{count}`"
            for channel_id, count in total_counts.items()
        )

        await self._respond(m, response)

    @count.command(name="mentions_per_message")
    async def mentions_per_message_count(self, ctx, *args):
        m = await ctx.reply("Loading...")

        mentions_counts, _ = await self._get_counts(
            guild=ctx.message.guild,
            search_string="",
            entities=(await ctx.guild.fetch_members()),
            message_transformer=None,
            name_transformer=lambda author: author.name,
            search_arg="mentions",
            status_update=self.count_status_update(m),
        )

        total_message_counts = self._get_message_count_cache(ctx.guild)
        if not total_message_counts:
            await ctx.reply(
                "No cache found! Build the cache with `build_cache` and try again"
            )
            return

        ratios: dict[str, float] = {}
        for (member_name, member), mentions in mentions_counts.items():
            if member is None:
                continue
            if str(member.id) not in total_message_counts:
                continue
            ratios[member_name] = mentions / total_message_counts[str(member.id)]

        ratios = self.sort_dict(ratios)

        response = "# Mentions Per Message\n"
        response += "\n".join(
            [
                f" - `{member_name}` has `{self.round_to_sig_figs(ratio)}` mentions / message"
                for member_name, ratio in ratios.items()
            ]
        )

        await self._respond(m, response)

    @count.command(name="compare")
    async def comparison_count(self, ctx, *queries):
        m = await ctx.reply("Loading...")

        counts = {}
        for query in queries:
            search: list[Message] = [
                m async for m in ctx.guild.search(content=query, limit=1)
            ]

            if search:
                counts[query] = search[0].total_results
            else:
                counts[query] = 0

        response = "# Comparisons \n"
        response += "\n".join(
            [f" - `{query}`: `{counts[query]}` messages" for query in counts]
        )

        counts = self.sort_dict(counts)
        await self._respond(m, response)

    @count.command(name="gex")
    async def emoji_dex_count(self, ctx: commands.Context):
        if not ctx.guild:
            return

        m = await ctx.reply("Loading...")

        queries = {emoji: f"<:{emoji.name}:{emoji.id}>" for emoji in ctx.guild.emojis}

        counts = {}
        individualdex = self.bot.get_user(1342265524075364545)
        for emoji, query in queries.items():
            search: list[Message] = [
                m
                async for m in ctx.guild.search(
                    content=query, authors=[individualdex], limit=1
                )
            ]

            if search:
                counts[emoji] = search[0].total_results
            else:
                counts[emoji] = 0

        response = "# Emojis \n"
        response += "\n".join(
            [
                f" - <:{emoji.name}:{emoji.id}>: `{counts[emoji]}` messages"
                for emoji in counts
            ]
        )

        counts = self.sort_dict(counts)
        await self._respond(m, response)

    @count.command(name="emojis")
    async def emoji_count(self, ctx: commands.Context):
        if not ctx.guild:
            return

        m = await ctx.reply("Loading...")

        queries = {emoji: f"<:{emoji.name}:{emoji.id}>" for emoji in ctx.guild.emojis}

        counts = {}
        for emoji, query in queries.items():
            search: list[Message] = [
                m async for m in ctx.guild.search(content=query, limit=1)
            ]

            if search:
                counts[emoji] = search[0].total_results
            else:
                counts[emoji] = 0

        response = "# Emojis \n"
        response += "\n".join(
            [
                f" - <:{emoji.name}:{emoji.id}>: `{counts[emoji]}` messages"
                for emoji in counts
            ]
        )

        counts = self.sort_dict(counts)
        await self._respond(m, response)

    @count.command(name="imagers")
    async def image_count(self, ctx):
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
            extra_args={"has": ["image"]},
            status_update=self.count_status_update(m),
        )

        response = f"# Images: {total}\n"
        response += "\n".join(
            [
                f" - `{member[0]}` has sent `{counts[member]}` images"
                for member in counts
            ]
        )

        await self._respond(m, response)

    def round_to_sig_figs(self, number, figs=3):
        return "{:g}".format(float("{:.{p}g}".format(number, p=figs)))

    @count.command(name="test_command")
    async def test_command(self, ctx, lines: int, len: int):
        await self._respond(ctx.message, ("o" * len) * lines)

    @count.command(name="per_capita")
    async def per_capita_count(self, ctx, *args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        total_counts = self._get_message_count_cache(ctx.guild)
        if not total_counts:
            await ctx.reply(
                "No cache found! Build the cache with `build_cache` and try again"
            )
            return

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=(await ctx.guild.fetch_members()),
            message_transformer=lambda message: message.author,
            name_transformer=lambda author: author.name,
            search_arg="authors",
            status_update=self.count_status_update(m),
        )

        rates: dict[tuple[str, User | Member], float] = {}
        for member, count in counts.items():
            if member[1] is None:
                continue
            if str(member[1].id) in total_counts:
                if total_counts[str(member[1].id)] == 0:
                    continue
                if count == 0:
                    continue
                rates[(member[0], member[1])] = count / total_counts[str(member[1].id)]

        rates = self.sort_dict(rates)

        response = f"# {search_string} per capita\n"
        response += "\n".join(
            [
                f" - `{member[0]}`: **{self.round_to_sig_figs(rates[member] * 100, 4)}%**"
                + f"  ->  {counts[member]}"
                for member in rates
            ]
        )

        await self._respond(m, response)

    @count.command(name="mentions")
    async def mentions_count(self, ctx):
        m = await ctx.reply("Loading...")

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string="",
            entities=(await ctx.guild.fetch_members()),
            message_transformer=None,
            name_transformer=lambda author: author.name,
            search_arg="mentions",
            status_update=self.count_status_update(m),
        )

        response = f"# Mentions: {total}\n"
        response += "\n".join(
            [
                f" - `{member[0]}` has been mentioned `{counts[member]}` times"
                for member in counts
            ]
        )

        await self._respond(m, response)

    @count.command(name="channels")
    async def channels_count(self, ctx, *args):
        m = await ctx.reply("Loading...")
        search_string = " ".join(args)

        counts, total = await self._get_counts(
            guild=ctx.message.guild,
            search_string=search_string,
            entities=ctx.guild.text_channels,
            message_transformer=lambda message: message.channel,
            name_transformer=lambda channel: (
                channel.name
                if isinstance(channel, discord.TextChannel)
                else "Unknown Channel"
            ),
            search_arg="channels",
            status_update=self.count_status_update(m),
        )

        if not search_string:
            self._store_guild_channel_counts(ctx.guild, counts)

        response = f"# {search_string}: {total}\n" if search_string else "# Channels\n"
        response += "\n".join(
            [f" - `{channel[0]}` has {counts[channel]} messages" for channel in counts]
        )

        await self._respond(m, response)

    @count.command(name="dates")
    async def dates(self, ctx, num_days: int):
        m = await ctx.reply("Loading...")

        days: list[date] = [date.today() - timedelta(days=n) for n in range(num_days)]

        day_bounds: list[tuple[date, datetime, datetime]] = [
            (day, datetime.combine(day, time.min), datetime.combine(day, time.max))
            for day in days
        ]

        day_bounds.reverse()

        counts: dict[date, int] = {}
        for day, day_start, day_end in day_bounds:
            search: list[Message] = [
                m
                async for m in ctx.guild.search(
                    limit=1, after=day_start, before=day_end
                )
            ]

            if search and search[0].total_results:
                counts[day] = search[0].total_results
            else:
                counts[day] = 0

        cache_path: Path = (
            CACHE_ROOT / f"day_message_count.{ctx.guild.id}.{round(time_ns() * 1000)}"
        )
        with open(cache_path, "w") as f:
            parsable_counts: dict[str, int] = {
                day.strftime("%F"): count for day, count in counts.items()
            }
            json.dump(parsable_counts, f)

        response = "# Day messages \n"
        response += "\n".join(
            [
                f" - `{day.strftime('%a, %D')}`: `{counts[day]}` messages"
                for day in counts
            ]
        )

        await self._respond(m, response)


async def setup(bot):
    await bot.add_cog(SearchCommands(bot))

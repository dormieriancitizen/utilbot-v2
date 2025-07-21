import ast
import contextlib
import io
from io import BytesIO
import asyncio
import re
import textwrap
import time
import traceback
from discord.ext import commands
import discord
from contextlib import redirect_stdout
from typing import Iterator, Sequence, Iterable

"""
This code is taken from
https://github.com/Ballsdex-Team/BallsDex-DiscordBot/blob/f7231670fe466835d0c7448f5ef47057ec2fde89/ballsdex/core/dev.py#L318
BallsDex-DiscordBot, which in turn took this code from
Cog-Creators and Danny

https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/dev_commands.py
https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/utils/chat_formatting.py
https://github.com/Rapptz/RoboDanny/blob/master/cogs/repl.py
Programming truely is a wonderful thing
"""


START_CODE_BLOCK_RE = re.compile(r"^((```py(thon)?)(?=\s)|(```))")


def box(text: str, lang: str = "") -> str:
    return f"```{lang}\n{text}\n```"


async def send_interactive(
    ctx: commands.Context,
    messages: Iterable[str],
    *,
    timeout: int = 15,
    time_taken: float | None = None,
    block: str | None = "py",
) -> list[discord.Message]:
    """
    Send multiple messages interactively.

    The user will be prompted for whether or not they would like to view
    the next message, one at a time. They will also be notified of how
    many messages are remaining on each prompt.

    Parameters
    ----------
    ctx : discord.ext.commands.Context
        The context to send the messages to.
    messages : `iterable` of `str`
        The messages to send.
    timeout : int
        How long the user has to respond to the prompt before it times out.
        After timing out, the bot deletes its prompt message.
    time_taken: float | None
        The time (in seconds) taken to complete the evaluation.

    Returns
    -------
    list[discord.Message]
        A list of sent messages.
    """
    result = 0

    def predicate(m: discord.Message):
        nonlocal result
        if (ctx.author.id != m.author.id) or ctx.channel.id != m.channel.id:
            return False
        try:
            result = ("more", "file").index(m.content.lower())
        except ValueError:
            return False
        else:
            return True

    messages = tuple(messages)
    ret = []

    for idx, page in enumerate(messages, 1):
        if block:
            text = box(page, lang=block)
        else:
            text = page
        if time_taken and idx == len(messages):
            time = (
                f"{round(time_taken * 1000)}ms"
                if time_taken < 1
                else f"{round(time_taken, 3)}s"
            )
            text += f"\n-# Took {time}"
        msg = await ctx.channel.send(text)
        ret.append(msg)
        n_remaining = len(messages) - idx
        if n_remaining > 0:
            if n_remaining == 1:
                prompt_text = (
                    "There is still one message remaining. Type {command_1} to continue"
                    " or {command_2} to upload all contents as a file."
                )
            else:
                prompt_text = (
                    "There are still {count} messages remaining. Type {command_1} to continue"
                    " or {command_2} to upload all contents as a file."
                )
            query = await ctx.channel.send(
                prompt_text.format(
                    count=n_remaining, command_1="`more`", command_2="`file`"
                )
            )
            try:
                resp = await ctx.bot.wait_for(
                    "message",
                    check=predicate,
                    timeout=15,
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(discord.HTTPException):
                    await query.delete()
                break
            else:
                try:
                    await ctx.channel.delete_messages((query, resp))  # type: ignore
                except (discord.HTTPException, AttributeError):
                    # In case the bot can't delete other users' messages,
                    # or is not a bot account
                    # or channel is a DM
                    with contextlib.suppress(discord.HTTPException):
                        await query.delete()
                if result == 1:
                    ret.append(
                        await ctx.channel.send(file=text_to_file("".join(messages)))
                    )
                    break
    return ret


def text_to_file(
    text: str,
    filename: str = "file.txt",
    *,
    spoiler: bool = False,
    encoding: str = "utf-8",
) -> discord.File:
    file = BytesIO(text.encode(encoding))
    return discord.File(file, filename, spoiler=spoiler)


def pagify(
    text: str,
    delims: Sequence[str] = ["\n"],
    *,
    priority: bool = False,
    shorten_by: int = 8,
    page_length: int = 2000,
) -> Iterator[str]:
    in_text = text
    page_length -= shorten_by
    while len(in_text) > page_length:
        this_page_len = page_length
        closest_delim = (in_text.rfind(d, 1, this_page_len) for d in delims)
        if priority:
            closest_delim = next((x for x in closest_delim if x > 0), -1)
        else:
            closest_delim = max(closest_delim)
        closest_delim = closest_delim if closest_delim != -1 else this_page_len
        to_send = in_text[:closest_delim]
        if len(to_send.strip()) > 0:
            yield to_send
        in_text = in_text[closest_delim:]

    if len(in_text.strip()) > 0:
        yield in_text


class DevCog(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""

    def __init__(self, bot):
        self._last_result = None
        self.sessions = {}
        self.env_extensions = {}
        self.bot = bot

    @staticmethod
    def async_compile(source, filename, mode):
        return compile(
            source, filename, mode, flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT, optimize=0
        )

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return START_CODE_BLOCK_RE.sub("", content)[:-3]

        # remove `foo`
        return content.strip("` \n")

    @classmethod
    def get_syntax_error(cls, e):
        """Format a syntax error to send to the user.

        Returns a string representation of the error formatted as a codeblock.
        """
        if e.text is None:
            return cls.get_pages("{0.__class__.__name__}: {0}".format(e))
        return cls.get_pages(
            "{0.text}\n{1:>{0.offset}}\n{2}: {0}".format(e, "^", type(e).__name__)
        )

    @staticmethod
    def get_pages(msg: str):
        """Pagify the given message for output to the user."""
        return pagify(msg, delims=["\n", " "], priority=True, shorten_by=25)

    @staticmethod
    def sanitize_output(ctx: commands.Context, input_: str) -> str:
        """Hides the bot's token from a string."""
        token = ctx.bot.http.token
        return re.sub(re.escape(token), "[EXPUNGED]", input_, re.I)

    def get_environment(self, ctx: commands.Context) -> dict:
        env = {
            "bot": ctx.bot,
            "ctx": ctx,
            "asyncio": asyncio,
            "discord": discord,
            "commands": commands,
            "text_to_file": text_to_file,
            "_": self._last_result,
            "__name__": "__main__",
        }
        for name, value in self.env_extensions.items():
            try:
                env[name] = value(ctx)
            except Exception as e:
                traceback.clear_frames(e.__traceback__)
                env[name] = e
        return env

    @commands.command(name="eval")
    async def _eval(self, ctx: commands.Context, *, body: str):
        """Execute asynchronous code.

        This command wraps code into the body of an async function and then
        calls and awaits it. The bot will respond with anything printed to
        stdout, as well as the return value of the function.

        The code can be within a codeblock, inline code or neither, as long
        as they are not mixed and they are formatted correctly.

        Environment Variables:
            ctx      - command invocation context
            bot      - bot object
            channel  - the current channel object
            author   - command author's member object
            message  - the command's message object
            discord  - discord.py library
            commands - redbot.core.commands
            _        - The result of the last dev command.
        """
        env = self.get_environment(ctx)
        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = "async def func():\n%s" % textwrap.indent(body, "  ")

        t1 = time.time()
        try:
            compiled = self.async_compile(to_compile, "<string>", "exec")
            exec(compiled, env)
        except SyntaxError as e:
            t2 = time.time()
            return await send_interactive(
                ctx, self.get_syntax_error(e), time_taken=t2 - t1
            )
        except Exception as e:
            t2 = time.time()
            await send_interactive(
                ctx,
                self.get_pages("{}: {!s}".format(type(e).__name__, e)),
                time_taken=t2 - t1,
            )
            return
        t2 = time.time()

        func = env["func"]
        result = None
        try:
            with redirect_stdout(stdout):
                result = await func()
        except Exception:
            printed = "{}{}".format(stdout.getvalue(), traceback.format_exc())
        else:
            printed = stdout.getvalue()
            await ctx.message.add_reaction("✅")

        if result is not None:
            self._last_result = result
            msg = "{}{}".format(printed, result)
        else:
            msg = printed
        msg = self.sanitize_output(ctx, msg)

        await send_interactive(ctx, self.get_pages(msg), time_taken=t2 - t1)


async def setup(bot):
    await bot.add_cog(DevCog(bot))

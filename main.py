import discord, os, asyncio
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands

import search

bot = commands.Bot(command_prefix='h!', self_bot=True)

@bot.command()
async def ping(ctx):
    await ctx.reply('pong')

@bot.command()
async def wait(ctx,time: int):
    await asyncio.sleep(time)
    await ctx.reply(f"Waited {time} seconds")

@bot.command()
async def icon(ctx, member: discord.Member):
    await ctx.reply(member.avatar)

@bot.command()
async def count(ctx,searchtype,*args):
    search_string = " ".join(args)
    if searchtype=="count":
        message_count = await search.get_messages_count(ctx.guild, search_string)
    elif searchtype=="user":
        for user in ctx.guild.members:
            print(user)
    await ctx.reply(str(message_count))

bot.run(os.getenv("TOKEN"))
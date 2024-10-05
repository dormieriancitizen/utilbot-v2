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
async def nuke(ctx, count: int):
    messages = [message async for message in ctx.channel.history(limit=count)]
    for message in messages:
        await message.delete()

@bot.command()
async def status(ctx, *args):
  activity = discord.Game(name=' '.join(args))
  await bot.change_presence(status=discord.Status.online, activity=activity)
  await ctx.message.delete()

@bot.command()
async def count(ctx,searchtype,*args):
    m = await ctx.reply("Loading...")

    search_string = " ".join(args)
    if searchtype=="count":
        message_count = await search.get_messages_count(ctx.guild, search_string)
        await ctx.reply(f"{message_count} messages")
        return
    elif searchtype=="user":
        counts = {}
        for member in (await ctx.guild.fetch_members()):
            member_count = await search.get_messages_count(ctx.guild, search_string, 
                                                           args=search.generate_search_arguments(author_id=str(member.id))
                                                           )
            counts[member.name] = member_count
        
        response = f"# {search_string if search_string else 'Users'}\n"
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        print(response)
        await m.edit(response)
        return
    elif searchtype=="channel":
        counts = {}
        for channel in ctx.guild.text_channels:
            channel_count = await search.get_messages_count(ctx.guild, search_string, 
                                                           args=search.generate_search_arguments(channel_id=str(channel.id))
                                                           )
            counts[channel.name] = channel_count
        response = f"# {search_string if search_string else 'Channels'}\n"
        response += "\n".join([f"-`{channel}` has {counts[channel]} messages" for channel in counts])
        print(response)
        await m.edit(response)
        return
    else:
        await m.edit(f"ERR: Searchtype {searchtype} does not exist.")


async def _spam(channel,string,count):
    if len(string) > 2000:
        raise Exception("String must be shorter than 2000 characters")

    for i in range(count):
        await channel.send(string)

@bot.command()
async def spam(ctx,count: int,*args):
    await ctx.message.delete()
    await _spam(ctx.channel," ".join(args), count)

@bot.command()
async def lag(ctx,count: int,channel=None):
    if channel is None:
        channel = ctx.channel
    else:
        channel = await discord.get_channel(channel)

    await _spam(channel,398*"🅰",count)

bot.run(os.getenv("TOKEN"))
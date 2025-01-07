import discord, os, asyncio
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands

import search, recursivestring, regex

bot = commands.Bot(command_prefix=os.getenv("PREFIX"), self_bot=True)

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
    def sort_dict(x):
        return dict(sorted(x.items(), key=lambda item: item[1]))
    
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

        counts=sort_dict(counts)

        response = f"# {search_string if search_string else 'Users'}\n"
        response += "\n".join([f"-`{member}` has sent `{counts[member]}` messages" for member in counts])
        print(response)
        await m.edit(response)
        return
    elif searchtype=="mentions":
        counts = {}
        for member in (await ctx.guild.fetch_members()):
            member_count = await search.get_messages_count(ctx.guild, search_string, 
                                                           args=search.generate_search_arguments(mentions=str(member.id))
                                                           )
            counts[member.name] = member_count

        counts=sort_dict(counts)

        response = f"# {search_string if search_string else 'Users'}\n"
        response += "\n".join([f"-`{member}` has been mentioned `{counts[member]}` times" for member in counts])
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

        counts=sort_dict(counts)

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

@bot.command("recurse")
async def recurse(ctx,recursive_type,*args):
    if recursive_type=="character":
        await ctx.message.edit(recursivestring.gen_recursive_string(" ".join(args)).rstrip())

@bot.command()
async def whitespace(ctx):
    await ctx.message.delete()
    await ctx.channel.send("‫"+"\n"*1998+"‫")

@bot.command()
async def spoil(ctx, *args):
    spoiled = "".join([f"||{x}||" for x in regex.findall(r'(.)'," ".join(args))])

    await ctx.message.edit(spoiled)

@bot.command()
async def archive_channels(ctx):
    await ctx.reply("U sure? if you are comment out the next line")
    return

    PREFIX = "archived-"
    channels = await ctx.guild.fetch_channels()

    for channel in channels:
        new_name = PREFIX+channel.name
        if not channel.name.startswith(PREFIX):
            await channel.edit(name=new_name)

    await ctx.reply("Done")

bot.run(os.getenv("TOKEN"))

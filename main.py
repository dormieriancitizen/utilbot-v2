import discord, os, asyncio
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands

import search, regex

bot = commands.Bot(command_prefix=os.getenv("PREFIX"), self_bot=True)

@bot.command()
async def icon(ctx, member: discord.Member):
    await ctx.reply(member.avatar)

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

# @bot.command("recurse")
# async def recurse(ctx,recursive_type,*args):
    # if recursive_type=="character":
        # await ctx.message.edit(recursivestring.gen_recursive_string(" ".join(args)).rstrip())

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

@bot.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded Cog: {filename[:-3]}")

if __name__=="__main__":
    bot.run(os.getenv("TOKEN"))
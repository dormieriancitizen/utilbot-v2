import os

from dotenv import load_dotenv
load_dotenv()

from discord.ext import commands

bot = commands.Bot(command_prefix=str(os.getenv("PREFIX")), self_bot=True)

# @bot.command("recurse")
# async def recurse(ctx,recursive_type,*args):
    # if recursive_type=="character":
        # await ctx.message.edit(recursivestring.gen_recursive_string(" ".join(args)).rstrip())
# 
# @bot.command()
# async def archive_channels(ctx):
    # await ctx.reply("U sure? if you are comment out the next line")
    # return
# 
    # PREFIX = "archived-"
    # channels = await ctx.guild.fetch_channels()
# 
    # for channel in channels:
        # new_name = PREFIX+channel.name
        # if not channel.name.startswith(PREFIX):
            # await channel.edit(name=new_name)
# 
    # await ctx.reply("Done")

@bot.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded Cog: {filename[:-3]}")

    for filename in os.listdir('./dropins'):
        if filename.endswith('.py'):
            await bot.load_extension(f'dropins.{filename[:-3]}')
            print(f"Loaded Dropin: {filename[:-3]}")

if __name__=="__main__":
    bot.run(str(os.getenv("TOKEN")))

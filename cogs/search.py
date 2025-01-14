from discord.ext import commands

class SearchCommands(commands.Cog):
    """Commands to deal with the searching of messages"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    @commands.command()
    async def count(self,ctx,searchtype,*args):
        def sort_dict(x):
            return dict(sorted(x.items(), key=lambda item: item[1]))
        
        m = await ctx.reply("Loading...")

        search_string = " ".join(args)
        if searchtype=="count":
            print(await ctx.channel.search(limit=1))
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

async def setup(bot):
    await bot.add_cog(SearchCommands(bot))    

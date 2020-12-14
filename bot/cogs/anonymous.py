from datetime import datetime

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog

class Anonymous(KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.rant_channel = None
        self.hidden = True

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = discord.utils.get(self.bot.guilds, id=311612862554439692)


        if (type(message.channel) is discord.channel.DMChannel and message.author in guild.members and message.author != self.bot.user):
            if message.content.startswith("RANT "):
                    
                # Kat Dev Server, testing-ground-1
                
                self.rant_channel = discord.utils.get(guild.channels, id=432214639305162752)
                
                embed = discord.Embed(colour=discord.Colour(0xcec0ce), description=message.clean_content)
                self.log.info(f"[RANT] Sent a rant. {message.author.id}")
                await self.rant_channel.send(embed=embed)
                
                await message.channel.send("Your rant has been successfully sent!\n\nThis message will delete after 60 seconds. You can safely remove your rant.\n\n*This command is completely anonymous, if people abuse this it will be removed!*", delete_after=60)
def setup(bot):
    bot.add_cog(Anonymous(bot))

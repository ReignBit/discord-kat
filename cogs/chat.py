
# discord specific imports
from discord.ext import commands
import discord

import utilities.KatCog as KatCog


class Chat(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user:
            if 'kat' in message.content.lower():
                
                if all(['good', 'job'], message.content.lower().split(' ')):
                    await message.channel.send("Thank you ;3")


def setup(bot):
    bot.add_cog(Chat(bot))
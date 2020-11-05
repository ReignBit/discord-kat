import discord
from discord.ext import commands

from utilities.KatCog import KatCog

class WarnSys(KatCog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def warn(self, ctx):
        """Shows your current warnings"""
        

def setup(bot):
    bot.add_cog(WarnSys(bot))

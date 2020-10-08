# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
import utilities.KatCog as KatCog

class Debug(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        0 / 0

    @commands.command()
    async def uncaught_test(self, ctx):
        await ctx.send(0 / 0)


def setup(bot):
    bot.add_cog(Debug(bot))
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
        self.hidden = True
    @commands.command()
    async def uncaught_test(self, ctx):
        await ctx.send(0 / 0)

    @commands.command()
    async def embed_test(self, ctx):
        dic = self.get_embed("common.embeds.debug_test")
        self.log.debug(dic)

        await ctx.send(embed=discord.Embed.from_dict(dic))


def setup(bot):
    bot.add_cog(Debug(bot))
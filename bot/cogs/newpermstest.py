# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
import utilities.KatCog as KatCog
import utilities.permissions as permissions

class Newpermstest(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot.check(self.check_perm)

    def check_perm(self, ctx):
        self.log.info("this works?")
        if permissions.has_permission(self.bot, ctx.author, ctx.channel, "Administrator"):
            return True

        # if command in guild.settings and has roleids
        #   if the roleid matches a roleid on user.



def setup(bot):
    bot.add_cog(Newpermstest(bot))

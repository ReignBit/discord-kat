# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
import utilities.KatCog as KatCog



class Badges(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.log.warn("Badge overhaul needed. Disabled for now.")
        #self.sql = levelutilities.LevelUtilities(bot.sql, self.log)
        

    # @commands.command()
    # async def badges(self, ctx, user:discord.User=None):
    #     """Show's a user's badges that have been awarded. $badges [user]"""
    #     if user is None:
    #         user = ctx.author

    #     badge_list = self.sql.get_badges(user.id)
    #     embed = discord.Embed(color=1233827)
    #     embed.set_author(name=f"{user.display_name}'s Badges", icon_url=user.avatar_url)
    #     if len(badge_list) == 0:
    #         embed.description = "You have not earned any badges yet!"
    #         await ctx.send(embed=embed)
    #         return
    #     else:
    
    #         for badge in badge_list:
    #             embed.add_field(name=badge['title'], value=badge['description'])

    #         await ctx.send(embed=embed)

    # @commands.command()
    # async def test_comd(self, ctx):
    #     _ = 10 / 0

def setup(bot):
    bot.add_cog(Badges(bot))
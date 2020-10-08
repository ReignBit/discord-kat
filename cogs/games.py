# discord specific imports
from discord.ext import commands
import discord
import ast

# python imports

# third party imports

# kat specific imports
import utilities.KatCog as KatCog
import utilities.kat_logger as kat_logger
class Games(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.command()
    async def test_embed(self, ctx, *, dic):
        self.log.info(dic)
        embed = discord.Embed.from_dict(ast.literal_eval(dic))
        self.log.info(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def __(self, ctx):
        TicTacToe(self.bot, ctx, ctx.author, None)

def setup(bot):
    bot.add_cog(Games(bot))




class TicTacToe:
    def __init__(self, bot, ctx, user_one, user_two):
        self.bot = bot
        self.log = kat_logger.Logger("Games.TicTacToe")
        self.ctx = ctx
        self.embed_msg = None
        self.user_one = user_one
        self.user_two = user_two
        self.bot.loop.create_task(self.create_game())

    async def create_game(self):
        embed = discord.Embed()
        embed.title = f"Tic Tac Toe Game"
        embed.description = f"Waiting for {self.ctx.author.name} to play!"

        embed.add_field(name='\u2800', value=':regional_indicator_x:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_o:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_x:', inline=True)

        embed.add_field(name='\u2800', value=':regional_indicator_o:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_x:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_o:', inline=True)

        embed.add_field(name='\u2800', value=':regional_indicator_x:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_o:', inline=True)
        embed.add_field(name='\u2800', value=':regional_indicator_x:', inline=True)

        embed.set_footer(text="ThisPersonsNameIsLong's turn!")
        await self.ctx.send(embed=embed)
        self.destroy()

    def destroy(self):
        del self
        
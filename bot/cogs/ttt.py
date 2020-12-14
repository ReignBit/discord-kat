import random

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog


class Ttt(KatCog):
    """Haistly written code for that one time Reign wanted to play Arma TTT"""
    def __init__(self, bot):
        super().__init__(bot)
        self.pct = 0.30

    @commands.command()
    async def set_pct(self, ctx, pct):
        if pct > 1 or pct < 0:
            await ctx.send("Percent must be between 0 and 1!")
            return
        
        self.pct = pct
        await ctx.send(f"Set traitor percent to {pct * 100}%")

    @commands.command()
    async def assign(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Not in Voice Channel.")
            return

        # set defaults
        traitor_amount = int(len(ctx.author.voice.channel.members) * self.pct)
        traitors = []

        players = []

        # role generation
        for member in ctx.author.voice.channel.members:
            if not member.bot:
                players.append(member)
        
        while traitor_amount > 0:
            for player in players:
                if random.random() > 0.6 and traitor_amount > 0:
                    traitors.append(player)
                    traitor_amount -= 1
        
        # role notification
        for player in players:
            if player in traitors:
                await player.send("You are a traitor!")
                self.log.info(f"Send role [TRAITOR] to [{player.display_name}]")
            else:
                await player.send("You are an innocent!")
                self.log.info(f"Send role [INNOCENT] to [{player.display_name}]")
        

        for traitor in traitors:
            string = ", ".join([x.display_name for x in traitors])
            await traitor.send("These are your traitorous friends: \n" + string)


def setup(bot):
    bot.add_cog(Ttt(bot))

# discord specific imports
from discord.ext import commands
import discord
# python imports
import requests
import json

# kat specific imports
import utilities.KatCog as KatCog
import utilities.utils as utils

# TODO: Use multiple API to get crypto coin rates
# TODO: Try to get the symbol instead of just the name. Might have to use another API to do this.



class Exchange(KatCog.KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.currencies = utils.read_resource("available_currencies.json")

    @commands.command(aliases=['ex'])
    async def exchange(self, ctx, amount: float, cur_from='USD', cur_to='GBP'):
        """Converts Currency ($exchange <amount> <from> <to>). Defaults to USD => GBP if none specified"""
        if ctx.invoked_subcommand is not None:
            return

        url = "https://api.exchangeratesapi.io/latest?symbols={}&base={}".format(cur_to, cur_from)

        result = json.loads(requests.get(url).text)
        self.log.debug(result)

        if 'error' in result:
            await ctx.send(result['error'])
            return

        rate = result['rates'][cur_to]

        embed = discord.Embed(title=":currency_exchange: Currency Exchange")
        embed.description = "Exchanging `{0}` `{1}` to `{2}`:\n **{3:.2f} {4}**".format(amount, cur_from, cur_to, (amount * float(rate)), cur_to)
        await ctx.send(embed=embed)

    @commands.command()
    async def exchange_list(self, ctx):
        """Shows all available exchange currencies"""
        embed = discord.Embed(title=":currency_exchange: Currency Exchange Available Currency Codes")
        embed.description = "Here are all the available currencies that can be converted:\n"

        for k,v in self.currencies.items():
            embed.description += "\n" + "**{}** : {}".format(k, v)
        await ctx.author.send(embed=embed)



def setup(bot):
    bot.add_cog(Exchange(bot))
from discord.ext import commands
import discord
import requests

from bot.utils.extensions import KatCog


class Destiny(KatCog):
    """Commands for interaction with Destiny 2's API"""

    def __init__(self, bot):
        super().__init__(bot)
        if self.settings["api-key"] == "":
            raise Exception("Destiny Cog missing setting `api-key`.")

    def _api_get(self, endpoint, **headers):
        resp = requests.get(
            self.settings["api-root"] + endpoint,
            headers={"X-API-Key": self.settings["api-key"]},
        )
        if resp.status_code == 200:
            return resp.json
        return None


def setup(bot):
    bot.add_cog(Destiny(bot))

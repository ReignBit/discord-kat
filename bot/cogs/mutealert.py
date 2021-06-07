from discord.ext import commands
import discord
import asyncio
import time

from bot.utils.extensions import KatCog
import bot.utils.constants as constants

class MuteAlert(KatCog):

    def __init__(self, bot):
        super().__init__(bot)

        self.suppress_list = {}

        self.bot.loop.create_background_task(self.background_check)

    async def background_check(self):
        for member in constants.Mutealert.ids:
            if member in self.suppress_list.keys() and time.time() - self.suppress_list.get(member) < constants.Mutealert.suppress_time:
                # Member has suppressed the alert. Skip.
                continue
            else:
                try:
                    del self.suppress_list[member]
                except:
                    pass
                obj_member = discord.utils.get(discord.utils.get(self.bot.guilds, id=constants.HomeGuild.ids[0]), id=member)
                if obj_member.voice:
                    if obj_member.self_mute:
                        member.send(":bell: You are muted! This will repeat every **5 seconds**. To suppress these notifications for 1 hour, in the server, type `$suppress`")
        asyncio.sleep(5)

    @commands.command
    async def suppress(self, ctx):
        if ctx.author.id in constants.Mutealert.ids:
            self.suppress_list[ctx.author.id] = time.time()

def setup(bot):
    bot.add_cog(MuteAlert(bot))

import datetime
import re

from discord.ext import commands
import discord


from bot.utils.extensions import KatCog
from bot.utils.converters import DateTimeConverter
from bot.utils.constants import GuildSettings


class Announce(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(aliases=["an"])
    async def announcement(self, ctx, *datetime: DateTimeConverter):
        if datetime:
            self.log.debug(datetime)
            await ctx.send(
                self.get_response("announce.command.announce.info", prefix=ctx.prefix)
            )

        guild = self.sql.ensure_exists(KatGuild, guild_id=ctx.guild.id)
        guild.get_setting(GuildSettings.announce_channel)

        self.log.debug(channel_id)
        self.log.debug(embed)

        if channel_id and embed:
            await ctx.guild.get_channel(channel_id).send(embed=embed)
            return
        await ctx.send(self.get_response("announce.command.announce.fail", prefix=ctx.prefix))

    def _announce_embed(self, guild_id, datetime):
        """Takes a guild id, a date and time, and returns
        an announcement embed for the guild along with the channel id

        Returns:
            :tuple: (channel_id: int, embed_json: dict)
        """

        guild = self.sql.ensure_exists("KatGuild", guild_id=guild_id)
        channel = guild.get_setting(GuildSettings.announce_channel, None)
        if channel is None:
            return None, None

        if validated_date and validated_time:
            # TODO: Add support for custom messages on the fly.
            settings = guild.get_setting(GuildSettings.announce_message, None)
            if settings:
                embed = discord.Embed.from_dict(settings)
                return channel, embed
        return None, None

    def _validate_date(self, date):
        try:
            datetime.datetime.strptime(date, "%d/%m/%y")
        except ValueError:
            return None

    def _validate_time(self, time):
        match = re.match(r"\d{2}:\d{2}", time)
        if match is None:
            return None
        return match.string


def setup(bot):
    bot.add_cog(Announce(bot))

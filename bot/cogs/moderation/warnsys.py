import time
from datetime import datetime

import discord
from discord.ext import commands

from bot.utils.extensions import KatCog


class Warn:
    def __init__(self, reason, timestamp, author, expires):
        self.reason = reason
        self.timestamp = time.time()
        self.timestr = datetime.fromtimestamp(
            self.timestamp).strftime("%m/%d/%Y, %H:%M:%S")

        self.author_id = author
        # TODO: Expire time?
        self.expires_at = datetime.fromtimestamp(
            self.timestamp).strftime("%m/%d/%Y, %H:%M:%S")

    @classmethod
    def from_dict(cls, data: dict):
        """Returns a Warn object created from dict"""
        return cls(data['reason'], data['timestamp'], data['author'], data['expires_at'])

    def to_dict(self):
        return {"timestamp": self.timestamp, "reason": self.reason, "author": self.author_id, "expires_at": self.expires_at}


class Warnsys(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

    def _create_warns_from_member(self, member: KatMember):
        if len(member.ensure_setting("warnsys.warns", [])) == 0:
            return None, 0

        _warns = []
        for warn in member.ensure_setting("warnsys.warns", []):
            _warns.append(Warn.from_dict(warn))
        return _warns, len(_warns)

    def _add_warning(self, member: KatMember, warn: Warn):
        warn_list = member.ensure_setting("warnsys.warns", [])
        warn_list.append(warn.to_dict())
        member.set_setting("warnsys.warns", warn_list)

    @commands.group()
    async def warns(self, ctx, user: discord.User=None):
        """Shows your current warnings"""
        if ctx.invoked_subcommand is not None:
            return

        if user is None:
            user = ctx.author

        member = self.sql.ensure_exists(
            "KatMember", guild_id=ctx.guild.id, user_id=user.id)
        warns, total_warns = self._create_warns_from_member(member)

        if total_warns == 0:
            await ctx.send(self.get_response("warnsys.error.no_warns"))
            return

        for warn in warns:
            username = "{}#{}".format(
                user.display_name, user.discriminator)
            avatar_url = user.avatar_url

            issuer = ctx.guild.get_member(warn.author_id)
            embed = discord.Embed.from_dict(self.get_embed(
                "warnsys.embeds.warn_self", username=username, reason=warn.reason, expires_at=warn.expires_at, issuer=issuer, avatar_url=avatar_url))

            await ctx.send(embed=embed)

    @warns.command(name="add")
    async def warn_add(self, ctx, user: discord.Member, *reason):
        """Adds a warning to a user with a reason"""
        if reason is None or reason == "" or len(reason) == 0:
            reason = ["No", "Reason."]

        warn = Warn(" ".join(reason), time.time(), ctx.author.id, 0)

        self._add_warning(self.sql.ensure_exists(
            "KatMember", guild_id=ctx.guild.id, user_id=user.id), warn)


def setup(bot):
    bot.add_cog(Warnsys(bot))

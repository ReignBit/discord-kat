from typing import List

from discord.ext import commands
import discord

from bot.utils.extensions import KatCog


class Poll:
    def __init__(self, msg_id, title, author: discord.Member, exp=-1):
        self.msg = msg_id
        self.title = title
        self.author = author
        self.exp = exp

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["msg"], data["title"], data["author"], data["exp"])

    def to_json(self):
        return {
            "msg": self.msg,
            "title": self.title,
            "author": self.author,
            "exp": self.exp,
        }


class Vote(KatCog):

    SETTING_VOTE_POLLS = "settings.vote.polls"

    def __init__(self, bot):
        super().__init__(bot)
        self.running_votes = self._get_all_guild_votes_from_db()

    def _get_all_guild_votes_from_db(self) -> dict:
        guild_polls = {}
        for guild in self.bot.guilds:
            poll = self._get_votes_from_db(guild.id)
            if poll:
                guild_polls[guild.id] = poll
        return guild_polls

    def _get_votes_from_db(self, guild: discord.Guild) -> List[Poll]:
        votes = self.sql.ensure_exists("KatGuild", guild_id=guild.id).ensure_setting(
            Vote.SETTING_VOTE_POLLS, {}
        )

        if len(votes) > 0:
            polls = []
            for vote in votes:
                polls.append(self._construct_poll(vote))
            return polls
        return None

    async def _create_new_poll(self, ctx, title) -> Poll:
        """Sends a new poll to the channel and returns a complete Poll object."""
        msg = await ctx.send(
            embed=self.get_embed(
                "vote.embeds.vote_started",
                owner=ctx.author,
                title=title,
                options=f"\nUse `{ctx.prefix}voteadd <option> to add options to this vote!`",
            )
        )

        return Poll(msg.id, title, author=ctx.author, exp=3600)

    @commands.command()
    def vote(self, ctx, *title: str):
        """Create a new poll"""
        poll = self._create_new_poll(ctx, title)

        current_polls = self._get_votes_from_db(ctx.guild)
        current_polls[ctx.guild.id].append(poll.to_json())

        self.sql.ensure_exists("KatGuild", guild_id=ctx.guild.id).set_setting(
            Vote.SETTING_VOTE_POLLS, current_polls
        )


def setup(bot):
    bot.add_cog(Vote(bot))

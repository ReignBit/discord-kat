# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
from utilities.KatCog import KatCog


class Misc(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.set_operator_level(KatCog.EVERYONE)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=2):
        """Clear up to <code>100</code> messages in a channel at a time. Messages must be younger than <code>14</code> days old."""
        amount += 1  # add one to make sure we also delete the response to the command.
        if amount > 100:
            # limit to 100 msgs at a time due to discord api rate limits.
            amount = 100

        # Get the history of the channel up to amount
        messages = await ctx.channel.history(limit=amount).flatten()

        try:
            # try to delete the messages.
            await ctx.channel.delete_messages(messages)
        # if we get a HTTP error then something has gone wrong and the clear has failed.
        except discord.errors.HTTPException as e:
            self.log.warn("Failed to delete message: " + str(e))
            await ctx.send(self.get_response("misc.error.clear_fail"), delete_after=10)
            return

        await ctx.send(self.get_response("misc.command.clear", amount=amount-1), delete_after=10)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *reason):
        """Kicks a user from the server. If no reason is provided then "No reason" is used."""
        if reason is None or reason == "" or len(reason) == 0:
            reason = ["No", "Reason."]

        # await ctx.guild.kick(member, reason)
        await ctx.send(self.get_response("misc.command.kick", member=member, reason=" ".join(reason), kicker=ctx.author))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *reason):
        """Bans a user from the server. If no reason is provided then "No reason" is used."""
        if reason is None or reason == "":
            reason = ["No", "Reason."]

        # await ctx.guild.ban(member, reason, delete_message_days=0)
        await ctx.send(self.get_response("misc.command.ban", member=member, reason=" ".join(reason), kicker=ctx.author))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def purge(self, ctx, member: discord.Member, *reason):
        """Bans a user from the server, and deletes all of their messages from the past 7 days. If no reason is provided then "No reason" is used.
        """
        if reason is None or reason == "":
            reason = ["No", "Reason."]

        # await ctx.guild.ban(member, reason, delete_message_days=7)
        await ctx.send(self.get_response("misc.command.purge", member=member, reason=" ".join(reason), kicker=ctx.author))


def setup(bot):
    bot.add_cog(Misc(bot))

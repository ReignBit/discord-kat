# discord specific imports
from discord.ext import commands
import discord

# python imports

# third party imports

# kat specific imports
from utilities.KatCog import KatCog

class ModerationMisc(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.set_operator_level(KatCog.MODERATORS)

    @commands.command()
    async def clear(self, ctx, amount=2):
        """Clear up to 100 messages in a channel at a time. Messages must be younger than 14 days old."""
        amount += 1 # add one to make sure we also delete the response to the command.
        if amount > 100: amount = 100  # limit to 100 msgs at a time due to discord api rate limits.
        
        messages = await ctx.channel.history(limit=amount).flatten() # Get the history of the channel up to amount
        
        try:
            await ctx.channel.delete_messages(messages)  # try to delete the messages.
        except discord.errors.HTTPException as e:   # if we get a HTTP error then something has gone wrong and the clear has failed.
            self.log.warn("Failed to delete message: " + str(e))
            await ctx.send(self.get_response("moderationmisc.error.clear_fail"), delete_after=10)
            return
    
        await ctx.send(self.get_response("moderationmisc.command.clear", amount=amount-1), delete_after=10)


    # TODO:
    #   - mute / unmute user
    #   - silence / unsilence a channel
    #   - warns?
    #   - 

    

def setup(bot):
    bot.add_cog(ModerationMisc(bot))
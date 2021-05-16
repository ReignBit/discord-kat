import math

from discord.ext import commands
import discord


from bot.utils.extensions import KatCog
from bot.utils.models import Member, Guild
from bot.utils import constants
import bot.utils.permissions as permissions


class Level(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        # This announcement attaches itself to $level and $leaderboard.
        # Use this to announce things todo with levels.
        self.announcement = ""
        self.ignore_chars = constants.Level.ignore_chars

        self.level_boundaries = {}
        self.generate_level_boundaries(1000)

        # Instance variables
        self.global_freeze = (
            False  # global level freeze. Overrides guild settings if set to True
        )

        self.debug_mode = True  # Extra verbosity when user's gain xp.

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Discord event. Fired every time a message is recieved from a guild. """
        if not msg.author.bot and not self.global_freeze:
            if not await self.check_guild_freeze_status(msg.guild.id):
                # If the message does not start with characters in settings.ignore_chars
                for chars in self.ignore_chars:
                    if msg.content.startswith(chars):
                        return

                await self.give_xp(msg)

    async def check_guild_freeze_status(self, guild_id: int):
        """Get's a guild's freeze status from the api"""
        guild = await Guild.get(guild_id, self.bot.session)
        return guild.ensure_setting(constants.GuildSettings.level_freeze, False)

    # Used only on cog_load. Not used for calculation, just for visual.
    def generate_level_boundaries(self, amount):
        """Generates level boundaries, used only for $level"""
        last_level = 0
        for x in range(1, amount):
            level = int((1 + math.sqrt(1 + 8 * (x * x) / 40)) / 2)
            if level > last_level:
                self.level_boundaries[level] = x * x
                last_level = level

    # Used when we need to award XP from message length.
    async def xp_algorithm(self, msglen, guild):
        return int(
            min(max((msglen / 0.9) * 0.3, 10), 200)
            * (await Guild.get(guild.id, self.bot.session)).ensure_setting(
                constants.GuildSettings.level_xp_multi, 1.0
            )
        )

    # The function that adds xp to user and calculates new levels.
    async def give_xp(self, message):
        member = await Member.get(message.guild.id, message.author.id, self.bot.session)
        curr_xp = member.xp
        curr_level = member.lvl

        awarded_xp = await self.xp_algorithm(len(message.clean_content), message.guild)
        new_xp = int(curr_xp + awarded_xp)
        new_level = self.calculate_level(new_xp)

        if curr_level is not new_level:
            await message.channel.send(
                "You leveled up! **Level `{}`**".format(new_level), delete_after=5
            )

        member.xp = new_xp
        member.lvl = new_level
        await member.save(self.bot.session)

    # Gets a level from xp amount
    def calculate_level(self, xp):
        return int((1 + math.sqrt(1 + 8 * (xp) / 40)) / 2)

    @commands.group()
    async def level(self, ctx):
        """Shows your current XP and level"""
        if ctx.invoked_subcommand is not None:
            # If the user is running a subcommand of level, then do nothing.
            return

        member = await Member.get(ctx.author.guild.id, ctx.author.id, self.bot.session)
        xp, level = member.xp, member.lvl
        self.log.debug(f"{xp} {level}")
        boundry = self.level_boundaries[int(level) + 1]

        embed = discord.Embed(color=constants.Color.soft_green)
        embed.set_author(
            name="{}'s Level".format(ctx.author.display_name),
            icon_url=ctx.author.avatar_url,
        )
        embed.description = ""
        if self.global_freeze or await self.check_guild_freeze_status(ctx.guild.id):
            embed.description += "⚠ Levels are currently frozen ⚠\n"
        if len(self.announcement) != 0:
            embed.description += self.announcement
        embed.add_field(
            name="Level `{}`".format(level), value="`{}xp / {}xp`".format(xp, boundry)
        )

        await ctx.send(embed=embed)

    # TODO: Implement this
    @commands.command()
    async def leaderboard(self, ctx):
        """Shows the guild's top 10 users with the most XP"""
        leaders = await Guild.members(ctx.guild.id, self.bot.session)
        leaders.sort(key=lambda x: x.xp, reverse=True)

        try:
            string = "\n\n**Username  |  Level  |   XP**    \n"
            for leader in leaders[:10]:
                username = ctx.guild.get_member(leader.user_id).display_name

                string += "{}. {}   |   `{}`/`{}`\n".format(
                    leaders.index(leader) + 1, username, leader.lvl, leader.xp
                )
        except Exception as e:
            self.log.exception(e)

        embed = discord.Embed(color=1233827)
        embed.set_author(
            name=f"Level Leaderboards for {ctx.guild.name}", icon_url=ctx.guild.icon_url
        )
        embed.description = self.announcement
        embed.description += string
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def level_freeze(self, ctx):
        if permissions.is_author(self.bot, ctx.author.id):
            self.global_freeze = not self.global_freeze
            self.log.info("GLOBAL LEVEL FREEZE SET TO: " + str(self.global_freeze))
            await ctx.send("Global Level Freeze: {}".format(self.global_freeze))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def level_announcement(self, ctx, *args):
        self.announcement = " ".join(args)
        await ctx.send("Set level announcement to:\n`{}`".format(" ".join(args)))


def setup(bot):
    bot.add_cog(Level(bot))

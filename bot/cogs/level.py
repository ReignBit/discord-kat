import math

from discord.ext import commands
import discord
import MySQLdb._exceptions

from bot.utils.extensions import KatCog
from bot.utils.models import KatMember
from bot.utils.constants import GuildSettings
import bot.utils.permissions as permissions


class Level(KatCog):
    def __init__(self, bot):
        super().__init__(bot)

        # This announcement attaches itself to $level and $leaderboard.
        # Use this to announce things todo with levels.
        self.announcement = ""
        self.ignore_chars = self.settings.get("ignore_chars")

        self.level_boundaries = {}
        self.generate_level_boundaries(1000)
        self.award_levels = {10: 5, 50: 6, 69: 7, 100: 8}

        # Instance variables
        self.global_freeze = (
            False  # global level freeze. Overrides guild settings if set to True
        )

        self.debug_mode = True  # Extra verbosity when user's gain xp.
        if self.bot.maintenance_mode:
            self.global_freeze = True
            self.debug_mode = True
            self.announcement = ":warning: Kat is undergoing Backend Maintenance :warning: \n" \
                ":snowflake: Global freeze due to maintenance :snowflake:"

    @commands.Cog.listener()
    async def on_maintenance_mode(self, value):
        if self.bot.maintenance_mode:
            self.global_freeze = True
            self.log.debug_mode = True
            self.announcement = ":warning: Kat is undergoing Backend Maintenance :warning: \n" \
                ":snowflake: Global freeze due to maintenance :snowflake:"
        else:
            self.global_freeze = False
            self.log.debug_mode = True
            self.announcement = ""

    @commands.Cog.listener()
    async def on_message(self, msg):
        """Discord event. Fired every time a message is recieved from a guild. """
        # If user is not a bot, and we are currently not in an ice age
        if not msg.author.bot and not self.global_freeze:
            # If the guild is not frozen
            if not self.check_guild_freeze_status(msg.guild.id):
                # If the message does not start with characters in settings.ignore_chars
                for chars in self.ignore_chars:
                    if msg.content.startswith(chars):
                        return

                await self.give_xp(msg)

    def check_guild_freeze_status(self, guild_id: int):
        """Get's a guild's freeze status from the DB"""
        try:
            guild = self.sql.ensure_exists("KatGuild", guild_id=guild_id)
            return guild.ensure_setting(GuildSettings.level_freeze, False)

        except MySQLdb._exceptions.IntegrityError:
            self.log.warn(
                "Failed to check guild freeze status for GID:{}".format(guild_id)
            )
            # If something goes wrong then freeze levels.
            return True

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
    def xp_algorithm(self, msglen, guild):
        return int(
            min(max((msglen / 0.9) * 0.3, 10), 200)
            * self.sql.ensure_exists("KatGuild", guild_id=guild.id).ensure_setting(
                GuildSettings.level_xp_multi, 1.0
            )
        )

    # The function that adds xp to user and calculates new levels.
    async def give_xp(self, message):

        member = self.sql.ensure_exists(
            "KatMember", guild_id=message.guild.id, user_id=message.author.id
        )
        curr_xp = member.xp
        curr_level = member.lvl

        awarded_xp = self.xp_algorithm(len(message.clean_content), message.guild)
        new_xp = int(curr_xp + awarded_xp)
        new_level = self.calculate_level(new_xp)

        if curr_level is not new_level:
            await message.channel.send(
                "You leveled up! **Level `{}`**".format(new_level), delete_after=5
            )

        member.xp = new_xp
        member.lvl = new_level

    # Gets a level from xp amount
    def calculate_level(self, xp):
        return int((1 + math.sqrt(1 + 8 * (xp) / 40)) / 2)

    @commands.group()
    async def level(self, ctx):
        """Shows your current XP and level"""
        if ctx.invoked_subcommand is not None:
            # If the user is running a subcommand of level, then do nothing.
            return

        member = self.sql.ensure_exists(
            "KatMember", guild_id=ctx.guild.id, user_id=ctx.author.id
        )

        xp, level = member.xp, member.lvl
        boundry = self.level_boundaries[int(level) + 1]

        embed = discord.Embed(color=1233827)
        embed.set_author(
            name="{}'s Level".format(ctx.author.display_name),
            icon_url=ctx.author.avatar_url,
        )
        embed.description = ""
        if self.global_freeze or self.check_guild_freeze_status(ctx.guild.id):
            embed.description += "⚠ Levels are currently frozen ⚠\n"
        if len(self.announcement) != 0:
            embed.description += self.announcement
        embed.add_field(
            name="Level `{}`".format(level), value="`{}xp / {}xp`".format(xp, boundry)
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx):
        """Shows the guild's top 10 users with the most XP"""
        self.log.debug("Leaderboard?")
        leaders = (
            self.sql.query("KatMember")
            .filter_by(guild_id=ctx.guild.id)
            .order_by(KatMember.xp)[:-11:-1]
        )
        self.log.debug(leaders)

        try:
            string = "\n\n**Username  |  Level  |   XP**    \n"
            for leader in leaders.copy():
                try:
                    username = ctx.guild.get_member(leader.user_id).display_name
                except AttributeError:
                    # Here we delete the user if we can't see them.
                    # However im unsure how this would work with +100 servers.
                    self.log.info(
                        "Deleting user_id {} from the DB.".format(leader.user_id)
                    )
                    self.sql.query("KatUser").filter_by(user_id=leader.user_id).delete()
                    leaders.pop(leaders.index(leader))

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

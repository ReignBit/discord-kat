from discord.ext import commands
import discord
import asyncio
import sys
import traceback
import json
import random
from string import Template


import utilities.KatLogger as KatLogger
import utilities.events
from utilities.KatClasses import KatGuild, KatMember, KatUser
import utilities.orm_utilities as orm_utilities
import utilities.utils as utils


class KatCog(commands.Cog):

    DEPENDENCIES = ['Core']

    # Operator level aliases
    EVERYONE = 0
    MODERATORS = 1
    ADMINISTRATORS = 2
    GUILD_OWNER = 3
    BOT_OWNER = 4

    def __init__(self, bot):
        self.dependencies = KatCog.DEPENDENCIES
        self.bot = bot

        self.sql = orm_utilities.SqlEngine()
        self.sql.create_sql_session()

        self.log = KatLogger.get_logger(self.qualified_name)
        self.bot.loop.create_task(self.create_help_file())

        # Load GLOBAL settings from config/
        self.load_settings()

        # operator level for permissions.
        self._operator_level = 0

        # Response Handling.
        self.responses = {}
        self.load_responses()

        # New EventManager stuff
        self.event_manager = utilities.events.EventManager(self.bot, cog=self)

        for cmd in self.walk_commands():
            self.log.info("Registered command %s" % cmd.qualified_name)

    def load_settings(self):
        try:
            self.settings = self.bot.settings['cogs'][self.qualified_name.lower(
            )]
        except KeyError:
            self.settings = {}

    def _fallback_setting(self, key):
        """Fetches fallback setting in case self.bot.settings returns KeyError"""
        # TODO: do this.
        pass

    def get_guild_setting(self, guild_id: discord.Guild, setting_key, default=None):
        """ 
            Attempt to retrieve a guild setting (setting_key) from the DB
            If the guild has no key for setting_key, then return default
        """
        self.log.debug("fetching guild_setting")
        guild_settings = self.sql.ensure_exists(
            "KatGuild", guild_id=guild_id).settings
        try:
            guild_settings = json.loads(guild_settings)
        except json.JSONDecodeError:
            return default

        _path = setting_key.split(".")
        _result = guild_settings
        for x in _path:
            _result = _result.get(x, {})
            self.log.debug(_result)
            if _result == {}:
                self.log.warning(
                    "Key {} doesn't exist in {}".format(x, guild_settings))
        return _result

    def get_guild_all_settings(self, guild_id):
        """
            Mostly for verbosity. Returns the JSON dict for a guild's settings
        """
        guild = self.sql.ensure_exists("KatGuild", guild_id=guild_id)
        try:
            guild_settings = json.loads(guild.settings)
        except json.JSONDecodeError:
            return guild, {}
        return guild, guild_settings

    def set_guild_setting(self, guild_id: discord.Guild, setting_key, value):
        guild, guild_json = self.get_guild_all_settings(guild_id)
        self._nested_set(guild_json, setting_key.split('.'), value)
        self.log.debug(guild_json)

        jsonified = json.dumps(guild_json)

        guild.settings = jsonified
        self.bot.sql_session.commit()

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_guild_setting(self, guild_id: discord.Guild, setting_key, default):
        """
            Checks if a guild_setting of setting_key exists. If not it creates the key with the value of default
        """
        _ = self.get_guild_setting(guild_id, setting_key)
        if _ == None:
            # guild setting doesnt exist
            self.set_guild_setting(guild_id, setting_key, default)

    # Response stuff

    def load_responses(self):
        # Load responses
        self.responses['common'] = utils.read_resource(
            "languages/english/common.json")
        self.log.info("Loaded responses for common")
        try:
            # Try to load any cog-specific responses
            # TODO: Per-guild languages
            self.responses[self.qualified_name.lower()] = \
                utils.read_resource(
                    "languages/english/{}.json".format(self.qualified_name.lower()))

            self.log.info("Loaded responses for {}".format(
                self.qualified_name))
        except (FileNotFoundError, IOError):
            self.log.warning(
                "Failed to load Cog-Specific language file for `{}`".format(self.qualified_name))

    def get_response(self, response, **args):
        _path = response.split(".")
        _result = self.responses
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                raise KeyError(
                    "Key {} doesn't exist in {}".format(x, response))
        choice = random.choice(_result).format(**args, cog=self, bot=self.bot)
        return choice

    def get_embed(self, embed, **kwargs):
        """Returns the embed JSON for embed, along with formatted args"""
        _path = embed.split(".")
        _result = self.responses
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                raise KeyError(
                    "Key {} doesn't exist in {}".format(x, embed))

        json_string = json.dumps(_result)

        t = Template(json_string)
        t = t.substitute(**kwargs)
        self.log.debug(t)
        _result = json.loads(t)
        return _result

    async def create_help_file(self):
        """Generates the help page for the cog. Used in the website's help page"""
        await asyncio.sleep(5)
        data = ""
        for command in self.walk_commands():
            if not command.hidden:
                if command.short_doc == "":
                    data += command.name + "||" + "No help provided." + "\n"
                else:
                    _ = command.short_doc.replace("<", "{")
                    _ = _.replace(">", "}")
                    data += command.name + "||" + _ + "\n"
        if len(data) > 0:
            with open('resources/kat_command_helps/' + self.qualified_name.lower(), 'w') as f:
                f.write(data)

    def set_operator_level(self, operator_level: int):
        if 0 > operator_level > 4:
            self.log.warn(
                "Operator level is not set correctly for this cog. Operator level will default to EVERYONE " /
                "meaning anyone can use all commands in this cog"
            )
            return AttributeError("Operator level must be between 0 and 4. Defaulting to EVERYONE.")

        self._operator_level = operator_level

    async def throw_command_error_to_message(self, ctx, error):
        exc_type, _, exc_traceback = sys.exc_info()
        self.log.warning(
            f"{ctx.command} encountered an error: {error} : {exc_type} {exc_traceback}")
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name="Command Failed",
                         icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1")
        embed.description = "```py\n{}\n```".format(
            traceback.format_exc(limit=2))
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.channel.send(self.get_response("common.error.missing_permissions", cmd=ctx.command))
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.channel.send(self.get_response("common.error.missing_args", args=error.param.name))
            return

        try:
            self.log.exception(error.original)
        except:
            pass
        self.log.warn("error: " + error)
        await ctx.channel.send(self.get_response('common.error.command_error'))

    # DAPI event
    async def cog_before_invoke(self, ctx):
        self.log.info(
            f"[USER {ctx.author.name} | {ctx.author.id}] [GUILD {ctx.guild.name} | {ctx.guild.id}] Performed {ctx.command}")

    async def cog_check(self, ctx) -> bool:
        """Only allow speficied roles to invoke the commands in this cog."""
        guild = self.sql.ensure_exists("KatGuild", guild_id=ctx.guild.id)
        # guild setting generation.
        roles = guild.ensure_setting("roles", {'moderators': [
                                     'moderator'], 'administrators': ['administrator', 'admin']})

        BOT_OWNER = [self.bot.app_info.owner.id]
        GUILD_OWNER = [self.bot.get_guild(guild.guild_id).owner.id] + BOT_OWNER
        ADMINISTRATOR_ROLES = roles['administrators']
        MODERATION_ROLES = roles['moderators'] + ADMINISTRATOR_ROLES

        # If operator_level is
        # 1 then all commands in the cog can be ran by moderators+.
        # 2 then all commands in the cog can be ran by only admin roles.
        # 3 then only the guild owner can run the commands.
        # 4 then only bot owner can run the commands.
        # 0 means any user can use these commands.

        try:
            if self._operator_level == KatCog.EVERYONE:
                return True

            if ctx.author.id in BOT_OWNER or ctx.author.id in GUILD_OWNER:
                return True

            elif self._operator_level == KatCog.MODERATORS:
                return await commands.has_any_role(*MODERATION_ROLES).predicate(ctx)

            elif self._operator_level == KatCog.ADMINISTRATORS:
                return await commands.has_any_role(*ADMINISTRATOR_ROLES).predicate(ctx)

            elif self._operator_level == KatCog.GUILD_OWNER:
                return GUILD_OWNER[0] == ctx.author.id

            elif self._operator_level == KatCog.BOT_OWNER:
                return BOT_OWNER[0] == ctx.author.id

        except commands.errors.MissingAnyRole:
            await ctx.send(self.get_response('common.error.permission_error'))
            return False

        except Exception as err:
            self.log.warn(err)

    def cog_unload(self):
        self.log.info(f"Unloading {self.qualified_name}")
        # New EventManager unload
        self.event_manager.destroy()
        # self.sql.destroy()
        self.run = False
        self.log.destroy()
        del self

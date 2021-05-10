"""Utility methods for loading and unload extensions"""
import gzip
import json
import sys
import os
import traceback
import random
import inspect
import importlib
import pkgutil
from typing import Iterator
from string import Template

import discord
from discord.ext import commands
from discord.ext.commands import errors, Cog

from bot.utils import logger, events


# TODO: Think about fragmenting this class.
class KatCog(commands.Cog):
    """discord.Cog extension for Kat support."""

    def __init__(self, bot):
        self.bot = bot

        self.log = logger.get_logger(self.qualified_name)

        # Response Handling.
        self.responses = {}
        self.load_responses()

        # New EventManager stuff
        self.event_manager = events.EventManager(self.bot, cog=self)

        for cmd in self.walk_commands():
            self.log.info("Registered command %s" % cmd.qualified_name)

    # Responses
    # TODO: This could also become like constants.responses?
    def load_responses(self):
        # Load responses
        self.responses["common"] = read_resource("/languages/english/common.json")
        self.log.info("Loaded responses for common")
        try:
            # Try to load any cog-specific responses
            # TODO: Per-guild languages
            self.responses[self.qualified_name.lower()] = read_resource(
                "/languages/english/{}.json".format(self.qualified_name.lower())
            )

            self.log.info("Loaded responses for {}".format(self.qualified_name))
        except (FileNotFoundError, IOError):
            self.log.warning(
                "Failed to load Cog-Specific language file for `{}`".format(
                    self.qualified_name
                )
            )

    def get_response(self, response, **args):
        _path = response.split(".")
        _result = self.responses
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                raise KeyError("Key {} doesn't exist in {}".format(x, response))
        choice = random.choice(_result).format(**args, cog=self, bot=self.bot)
        return choice

    # TODO: same here?
    def get_embed(self, embed, **kwargs) -> dict:
        """Returns the embed JSON for embed, along with formatted args"""
        _path = embed.split(".")
        _result = self.responses
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                raise KeyError("Key {} doesn't exist in {}".format(x, embed))

        json_string = json.dumps(_result)

        t = Template(json_string)
        t = t.substitute(**kwargs)
        self.log.debug(t)
        _result = json.loads(t)
        return _result

    async def throw_command_error_to_message(self, ctx, error):
        exc_type, _, exc_traceback = sys.exc_info()
        self.log.warning(
            f"{ctx.command} encountered an error: {error} : {exc_type} {exc_traceback}"
        )
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(
            name="Command Failed",
            icon_url="https://cdn.discordapp.com/emojis/669531431428685824.png?v=1",
        )
        embed.description = "```py\n{}\n```".format(traceback.format_exc(limit=2))
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            await ctx.channel.send(
                self.get_response("common.error.missing_permissions", cmd=ctx.command)
            )
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.channel.send(
                self.get_response("common.error.missing_args", args=error.param.name)
            )
            return

        if isinstance(error, commands.MemberNotFound):
            await ctx.channel.send(
                self.get_response("common.error.member_not_found", error=error.argument)
            )
            return

        try:
            self.log.exception(error.original)
        except Exception:
            pass
        self.log.warn("error: " + str(error))
        self.log.warn(str(type(error)))
        await ctx.channel.send(self.get_response("common.error.command_error"))

    async def cog_before_invoke(self, ctx):
        self.log.info(
            f"[USER {ctx.author.name} | {ctx.author.id}] [GUILD {ctx.guild.name}"
            f" | {ctx.guild.id}] Performed {ctx.command}"
        )

    def cog_unload(self):
        self.log.info(f"Unloading {self.qualified_name}")
        self.run = False
        self.event_manager.destroy()
        self.log.destroy()
        del self


def unqualify(name: str) -> str:
    """Return an unqualified name given a qualified module/package `name`."""
    return name.rsplit(".", maxsplit=1)[-1]


def walk_extensions() -> Iterator[str]:
    """Yield extension names from the cogs subpackage."""
    # Avoid circular import.
    from bot import cogs

    def on_error(name: str):
        raise ImportError(name=name)

    for module in pkgutil.walk_packages(
        cogs.__path__, f"{cogs.__name__}.", onerror=on_error
    ):
        if unqualify(module.name).startswith("_"):
            # Ignore module/package names starting with an underscore.
            continue

        if module.ispkg:
            imported = importlib.import_module(module.name)
            if not inspect.isfunction(getattr(imported, "setup", None)):
                # If it lacks a setup function, it's not an extension.
                continue

        yield module.name


def load_cog(bot, cog_name) -> Cog:
    """Attempts to load a cog from 'cogs/'"""
    try:
        matches = get_cog_name_matches(cog_name)

        loaded = []
        for cog in matches:
            bot.load_extension(cog)
            if bot.get_cog(cog.split(".")[-1].capitalize()):
                loaded.append(bot.get_cog(cog.split(".")[-1].capitalize()))

            return cog_name, loaded

        raise errors.ExtensionNotFound

    except errors.ExtensionError as err:
        bot.log.warn("Failed to load Cog: %s" % cog_name)
        bot.log.warn("re-raising exception: %s" % err.__cause__)
        raise err


def get_cog_name_matches(cog_name):
    matches = []
    for extension in walk_extensions():
        if cog_name in extension:
            matches.append(extension)
    return matches


def unload_cog(bot, cog_name) -> Cog:
    """Attempts to unload a cog from 'cogs/'"""

    try:
        # Find extension
        matches = get_cog_name_matches(cog_name)
        if len(matches) > 1:
            raise errors.ExtensionNotFound(
                f"Ambiguous extension name. Choose between the following:\n{matches}"
            )

        old_cog = bot.get_cog(matches[0])
        bot.unload_extension(matches[0])
        bot.log.info("Unloaded %s" % cog_name)
        return cog_name, old_cog

    except errors.ExtensionError as err:
        bot.log.crit("Failed to unload Cog: %s" % cog_name)
        bot.log.crit("re-raising exception: %s" % err)
        raise err


def compress_file(path):
    """Takes a file and compresses it using g-zip, returns bytes"""
    with open(path, "rb") as f:
        compressed = gzip.compress(f.read())
    return compressed


def read_resource(filepath: str):
    """Read data from a resource file filepath located in bot/resources/"""
    if os.path.exists("bot/resources/" + filepath):
        with open("bot/resources/" + filepath, "r", encoding="utf-8") as f:
            return json.load(f)


def write_resource(filepath: str, data):
    """Write data to a resource file filepath located in bot/resources/"""
    with open("bot/resources/" + filepath, "w") as f:
        f.write(data)


def calculate_lines():
    """ Goes through every file in bot.cogs/ and bot.utils/ and counts the lines. Used for presence"""

    def _calc(file_path) -> int:
        """Recursively search through file_path and count all file lines"""
        lines = 0
        for file in os.listdir(file_path):
            if os.path.isdir(file_path + "/" + file) and "__" not in file:
                # self.log.debug("is directory: " + file_path + "/" + file)
                lines += _calc(file_path + "/" + file)
            else:
                if "__" not in file or "logs" not in file and file.endswith(".py"):
                    try:
                        # self.log.debug("counting file: " + file_path + "/" + file)
                        lines += sum(
                            1
                            for line in open(
                                file_path + "/" + file, encoding="utf-8"
                            )
                        )
                        # self.log.debug(lines)
                    except (IOError, PermissionError):
                        pass
        return lines

    count = _calc("bot/cogs") + _calc("bot/utils")
    return count

from typing import Optional, List
import logging
import os
from collections.abc import Mapping

import yaml

log = logging.getLogger(__name__)


# Copied from https://github.com/python-discord/bot/blob/main/bot/constants.py
def _recursive_update(original, new):
    """
    Helper method which implements a recursive `dict.update`
    method, used for updating the original configuration with
    configuration specified by the user.
    """

    for key, value in original.items():
        if key not in new:
            continue

        if isinstance(value, Mapping):
            if not any(isinstance(subvalue, Mapping) for subvalue in value.values()):
                original[key].update(new[key])
            _recursive_update(original[key], new[key])
        else:
            original[key] = new[key]


with open('config/config_default.yml') as f:
    _CONFIG_YAML = yaml.safe_load(f)


if os.path.exists("config/config.yml"):
    log.info("User config file exists. Loading contents...")
    with open("config/config.yml") as f:
        user_config = yaml.safe_load(f)
    _recursive_update(_CONFIG_YAML, user_config)


class YAMLGetter(type):
    subsection = None

    def __getattr__(cls, name):
        name = name.lower()
        try:
            if cls.subsection is not None:
                return _CONFIG_YAML[cls.section][cls.subsection][name]
            return _CONFIG_YAML[cls.section][name]
        except KeyError:
            path = ".".join(
                (cls.section, cls.subsection, name)
                if cls.subsection is not None else(cls.section, name)
                )
            log.critical(f"Tried to access config variable at `{path}`, but could not be found!")

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


# Data classes
class Bot(metaclass=YAMLGetter):
    section = "bot"

    token: str
    def_prefix: str
    startup_cogs: Optional[List[str]]
    maintenance_mode: bool


class HomeGuild(metaclass=YAMLGetter):
    """Constants for our Discord Guild's use"""
    section = "home_guilds"

    ids: List[int]
    channels: List[int]


class Logger(metaclass=YAMLGetter):
    section = "logger"
    compress: bool
    level: int
    filename: str


class Api(metaclass=YAMLGetter):
    section = "api"
    url: str
    auth_type: str
    token: str


#  Cog specific data classes
class Core(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "core"

    restart_message_guild_id: int
    restart_message_client_id: int
    ensure_file_integrity: Optional[List[str]]


class Orwell(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "orwell"

    host: str
    user: str
    paswd: str
    allowed_roles: List[int]


class Milsim(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "orwell"

    op_name: str


class Twitch(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "twitch"

    host: str
    clientid: str
    secret: str


class Level(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "level"

    ignore_chars: Optional[List[str]]


class Configurator(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "configurator"

    banned_prefix_chars: List[str]


class Fun(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "fun"

    api_key: str
    anon_key: str


class Dyndns(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "dyndns"

    key: str
    domain: str


class Mutealert(metaclass=YAMLGetter):
    section = "cogs"
    subsection = "mutealert"

    suppress_time: int
    ids: List[int]


class EventManager(metaclass=YAMLGetter):
    section = "event_manager"

    max_event_timer: int
    debug: bool

    events: List[dict]


# End of cog specific data classes
class Colour(metaclass=YAMLGetter):
    section = "colours"

    blue: int
    bright_green: int
    orange: int
    pink: int
    purple: int
    soft_green: int
    soft_orange: int
    soft_red: int
    white: int
    yellow: int
    invisble: int


class GuildSettings(metaclass=YAMLGetter):
    section = "guild_settings"

    prefix: str
    announce_channel: str
    announce_message: str
    fun_counter: str
    level_freeze: str
    level_xp_multi: str
    roles_moderators: str
    roles_admins: str


class Color(Colour):
    """Alias for Colours"""
    pass

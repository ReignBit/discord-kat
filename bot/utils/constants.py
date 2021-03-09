class Colour:

    blue: int = 0x3775a8
    bright_green: int = 0x01d277
    orange: int = 0xe67e22
    pink: int = 0xcf84e0
    purple: int = 0xb734eb
    soft_green: int = 0x68c290
    soft_orange: int = 0xf9cb54
    soft_red: int = 0xcd6d6d
    white: int = 0xfffffe
    yellow: int = 0xffd241
    invisble: int = 0x2f3136


class Color(Colour):
    """Alias for Colours"""
    pass


class GuildSettings:
    prefix: str = "settings.prefix"
    announce_channel: str = "settings.announce.channel"
    announce_message: str = "settings.announce.message"
    fun_counter: str = "settings.fun.chighscore"
    level_freeze: str = "settings.level.freeze"
    level_xp_multi: str = "settings.level.xp_multi"
    roles_moderators: str = "roles.moderators"
    roles_admins: str = "roles.administrators"

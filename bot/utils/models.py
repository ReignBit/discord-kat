"""Database model classes"""
import datetime
import json

from bot.utils import constants


DEFAULT_SETTINGS = {"settings": {"prefix": constants.Bot.def_prefix}}


class Guild:
    """Guild information from Kat API."""

    __slots__ = "guild_id", "_settings"

    def __init__(self, id, _settings: dict):
        self.guild_id = id
        self._settings: dict = _settings

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["id"], dict(data["settings"]))

    @classmethod
    async def get(cls, id, session):
        data = await session.get("guilds/" + str(id))
        if data[0]:
            return cls.from_dict(data[0])
        else:
            return cls.from_dict({"id": id, "settings": DEFAULT_SETTINGS})

    @classmethod
    async def members(cls, id, session):
        data = await session.get(f"guilds/{id}/members")
        if data:
            members = []
            for member in data:
                members.append(Member.from_dict(member))
            return members

    @property
    def id(self):
        return self.guild_id

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    @property
    def prefix(self):
        return self.ensure_setting(constants.GuildSettings.prefix, "$")

    @prefix.setter
    def prefix(self, new_prefix):
        self.set_setting(constants.GuildSettings.prefix, new_prefix)

    @property
    def settings(self):
        """Return Guild settings as a JSONDict."""
        return self._settings

    @settings.setter
    def settings(self, new_settings: dict):
        """Set Guild settings as `dict`."""
        self._settings = new_settings

    async def save(self, session):
        await session.patch("guilds/" + str(self.guild_id), self.__repr__())

    def get_setting(self, setting_key):
        """Gets the value at `setting_key`. If it doesn't exist then returns `None`."""
        _path = setting_key.split(".")
        _result = self.settings
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                return None
        return _result

    def get_raw_settings(self) -> str:
        """Return string of guild settings."""
        return self.settings

    def set_setting(self, setting_key, value):
        """Adds/Overwrites the current `setting_key` with `value`
        If `setting_key` doesn't exist then it is created.

        Returns `value`.
        """
        _lst = self.settings
        self._nested_set(_lst, setting_key.split("."), value)
        self.settings = json.dumps(_lst)
        return value

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_setting(self, setting_key, value):
        """Ensure that `setting_key` exists, if not then set's default to `value`."""
        result = self.get_setting(setting_key)
        if result is None:
            result = self.set_setting(setting_key, value)
        return result

    def __str__(self):
        return "<KatGuild (id={}, prefix={}, settings={})>".format(
            self.guild_id, self.prefix, self.settings
        )

    def __repr__(self):
        # TODO: For some reason self.settings here is a str instead
        # of a dict. I have no idea why... For now we just json.loads it.
        return {"id": self.id, "settings": json.loads(self.settings)}


class User:
    """User information from Kat API."""

    def __init__(self, id, birthday="None", birthday_years=0):
        self.user_id: int = id
        self.birthday_years: int = birthday_years
        self.birthday = (
            datetime.datetime.strptime(birthday, "%Y-%m-%d")
            if birthday != "None"
            else None
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["id"],
            birthday=data.get("birthday", None),
            birthday_years=data.get("years", 0),
        )

    def to_json(self):
        return self.__repr__()

    @property
    def id(self):
        return self.user_id

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    @classmethod
    async def get(cls, id, session):
        data = await session.get("users/" + str(id))
        if data[0]:
            return cls.from_dict(data["data"][0])
        else:
            return cls.from_dict({"id": id})

    async def save(self, session):
        await session.patch("users/" + str(self.user_id), self.to_json())

    def __str__(self):
        return "<User (id={})>".format(self.user_id)

    def __repr__(self):
        return {
            "id": self.user_id,
            "birthday": self.birthday.strftime("%Y-%m-%d") if self.birthday else None,
            "years": self.birthday_years,
        }


class Member:
    """Member information from Kat DB.

    `guild_id`:int  ;Guild ID of which the member belongs to

    `user_id`:int   ;ID of the user of which the member belongs to

    `_data`:dict    ;JSON dict of member-data. (for now just includes warning system data.
    """

    def __init__(self, gid, uid, lvl, xp, settings=""):
        self.guild_id = gid
        self.user_id = uid
        self._settings = settings

        self.xp = xp
        self.lvl = lvl

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["gid"],
            data["id"],
            data.get("level", 0),
            data.get("xp", 0),
            data.get("settings", {}),
        )

    @classmethod
    async def get(cls, gid, uid, session):
        data = await session.get(f"guilds/{gid}/{uid}")
        if data[0]:
            return cls.from_dict(data[0])
        else:
            return cls.from_dict({"gid": gid, "id": uid, "level": 0, "xp": 0})

    @property
    def id(self):
        return (self.guild_id, self.user_id)

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    def set_xp(self, value):
        self.xp = value

    @property
    def settings(self):
        """Return Guild settings as a JSONDict."""
        return self._settings

    @settings.setter
    def settings(self, new_settings: dict):
        """Set Guild settings as `str`."""
        self._settings = new_settings

    def get_setting(self, setting_key):
        """Gets the value at `setting_key`. If it doesn't exist then returns `None`."""
        _path = setting_key.split(".")
        _result = self.settings
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                return None
        return _result

    def get_raw_settings(self) -> str:
        """Return string of member settings."""
        return self.settings

    def set_setting(self, setting_key, value):
        """Adds/Overwrites the current `setting_key` with `value`
        If `setting_key` doesn't exist then it is created.

        Returns `value`.
        """
        _lst = self.settings
        self._nested_set(_lst, setting_key.split("."), value)
        self.settings = json.dumps(_lst)
        return value

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_setting(self, setting_key, value):
        """Ensure that `setting_key` exists, if not then set's default to `value`."""
        result = self.get_setting(setting_key)
        if result is None:
            result = self.set_setting(setting_key, value)
        return result

    async def save(self, session):
        await session.patch(f"guilds/{self.guild_id}/{self.user_id}", self.__repr__())

    def __str__(self):
        return "<Member (guild_id={}, user_id={}, (xp={},lvl={}))>".format(
            self.guild_id, self.user_id, self.xp, self.lvl
        )

    def __repr__(self):
        return {
            "id": self.user_id,
            "gid": self.guild_id,
            "level": self.lvl,
            "xp": self.xp,
            "settings": self.settings,
        }

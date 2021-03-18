"""Database model classes"""
import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, Date, ForeignKey, TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


Base = declarative_base()


class KatGuild(Base):
    """Guild information from Kat DB."""
    __tablename__ = "guild_data"

    guild_id = Column("guild_id", BigInteger, primary_key=True)
    _settings = Column("guild_settings", TEXT())

    @property
    def id(self):
        return self.guild_id

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    @hybrid_property
    def prefix(self):
        return self.ensure_setting("settings.prefix", "$")

    @prefix.setter
    def prefix(self, new_prefix):
        self.set_setting("settings.prefix", new_prefix)

    @hybrid_property
    def settings(self):
        """Return Guild settings as a JSONDict."""
        try:
            _ = json.loads(self._settings)
        except json.JSONDecodeError:
            return {}
        return _

    @settings.setter
    def settings(self, new_settings: str):
        """Set Guild settings as `str`."""
        try:
            json.loads(new_settings)
        except json.JSONDecodeError:
            self._settings = {}
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
        """Return string of guild settings."""
        return self.settings

    def set_setting(self, setting_key, value):
        """Adds/Overwrites the current `setting_key` with `value`
            If `setting_key` doesn't exist then it is created.

            Returns `value`.
        """
        _lst = self.settings
        self._nested_set(_lst, setting_key.split('.'), value)
        self.settings = json.dumps(_lst)
        return value

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_setting(self, setting_key, value):
        """Ensure that `setting_key` exists, if not then set's default to `value`.
        """
        result = self.get_setting(setting_key)
        if result == None:
            result = self.set_setting(setting_key, value)
        return result

    def __repr__(self):
        return "<KatGuild (id={}, prefix={}, settings={})>".format(self.guild_id, self.prefix, self.settings)


class KatUser(Base):
    """User information from Kat DB."""
    __tablename__ = "user_data"

    user_id = Column("user_id", BigInteger, primary_key=True)
    birthday = Column(Date, default=None)
    birthday_years = Column(Integer, default=0)

    @property
    def id(self):
        return self.user_id

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    def __repr__(self):
        return "<User (id={})>".format(self.user_id)


class KatMember(Base):
    """ Member information from Kat DB.

        `guild_id`:int  ;Guild ID of which the member belongs to

        `user_id`:int   ;ID of the user of which the member belongs to

        `_data`:dict    ;JSON dict of member-data. (for now just includes warning system data.
    """
    __tablename__ = "member_data"

    guild_id = Column(BigInteger, ForeignKey('guild_data.guild_id'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('user_data.user_id'), primary_key=True)
    _settings = Column("data", TEXT)

    xp = Column(Integer, default=1)
    lvl = Column(Integer, default=1)

    user = relationship("KatUser")
    guild = relationship("KatGuild")

    @property
    def id(self):
        return (self.guild_id, self.user_id)

    @id.setter
    def id(self, value):
        raise Exception("id is a read-only property!")

    def set_xp(self, value):
        self.xp = value

    ####

    @hybrid_property
    def settings(self):
        """Return Guild settings as a JSONDict."""
        try:
            _ = json.loads(self._settings)
        except json.JSONDecodeError:
            return {}
        except TypeError:
            return {}

        return _

    @settings.setter
    def settings(self, new_settings: str):
        """Set Guild settings as `str`."""
        try:
            json.loads(new_settings)
        except json.JSONDecodeError:
            self._settings = {}
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
        self._nested_set(_lst, setting_key.split('.'), value)
        self.settings = json.dumps(_lst)
        return value

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_setting(self, setting_key, value):
        """Ensure that `setting_key` exists, if not then set's default to `value`.
        """
        result = self.get_setting(setting_key)
        if result == None:
            result = self.set_setting(setting_key, value)
        return result

    def __repr__(self):
        return "<Member (guild_id={}, user_id={}, (xp={},lvl={}))>".format(self.guild_id, self.user_id, self.xp, self.lvl)

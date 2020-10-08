import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event, Column, Integer, String, BigInteger, BLOB, Date, ForeignKey, null, TEXT
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
import json
Base = declarative_base()
class KatGuild(Base):
    """Guild information from Kat DB."""
    __tablename__ = "guild_table"

    guild_id = Column("guild_id", BigInteger, primary_key=True)
    prefix = Column(String, default="$")
    _settings = Column("guild_settings", TEXT(convert_unicode=True))


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
        _path = setting_key.split(".")
        _result = self.settings
        for x in _path:
            _result = _result.get(x, {})
            if _result == {}:
                return None
        return _result
        
    def get_raw_settings(self):
        """Return string of guild settings."""
        return self.settings
    
    def set_setting(self, setting_key, value):
        _lst = self.settings
        self._nested_set(_lst, setting_key.split('.'), value)
        self.settings = json.dumps(_lst)
        return value


    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

    def ensure_setting(self, setting_key, value):
        result = self.get_setting(setting_key)
        if result == None:
            result = self.set_setting(setting_key, value)
        return result


    def __repr__(self):
        return "<KatGuild (id={}, prefix={}, settings={})>".format(self.guild_id, self.prefix, self.settings)

class KatUser(Base):
    """User information from Kat DB."""
    __tablename__ = "user_table"

    user_id = Column("user_id", BigInteger, primary_key=True)
    birthday = Column(Date, default=None)
    birthday_years = Column(Integer, default=0)

    def __repr__(self):
        return "<User (id={})>".format(self.user_id)

class KatMember(Base):
    
    """Member information from Kat DB."""
    __tablename__ = "level_data"

    guild_id = Column(BigInteger, ForeignKey('guild_table.guild_id'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('user_table.user_id'), primary_key=True)
    #TODO: Use getters and setter protection for these.
    xp = Column(Integer, default=1)
    lvl = Column(Integer, default=1)
    
    user = relationship("KatUser")
    guild = relationship("KatGuild")

    def set_xp(self, value):
        self.xp = value

    def __repr__(self):
        return "<Member (guild_id={}, user_id={}, (xp={},lvl={}))>".format(self.guild_id, self.user_id, self.xp, self.lvl)

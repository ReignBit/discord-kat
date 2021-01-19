import json
import logging


class Settings:
    """A data class that looks for a value in dict1 before checking dict2.

        `get(key)`; returns value from `_settings_dict`,
            attempts to retrieve key from `_fallback_dict` if does not exist in `_settings_dict`.

        `set(key, value)`; sets value to key in `_settings_dict`.
    """

    def __init__(self, config_data: dict = None, fallback_data: dict = None):
        self._settings_dict = {}
        self._fallback_dict = {}

        if config_data:
            self._settings_dict = config_data
        if fallback_data:
            self._fallback_dict = fallback_data

    @classmethod
    def from_file(cls, config_file, fallback_file):
        cls = cls()
        with open(config_file, "r") as f:
            try:
                cls._settings_dict = json.load(f)
            except json.DecodeError:
                cls._settings_dict = {}

        with open(fallback_file, "r") as f:
            try:
                cls._fallback_dict = json.load(f)
            except json.DecodeError:
                cls.__fallback_dict = {}
                logging.log(
                    "Failed to retrieve fallback settings. "
                    "Please ensure the `config_default.json` file in `config/` "
                    "is formatted correctly."
                )
        return cls

    def from_key(self, key):
        """Returns a new class from an existing instance with data from a key."""
        try:
            settings_ = self.get(key)
        except KeyError:
            settings_ = {}
        fallback_ = ""

        _result = None
        try:
            for x in key.split("."):
                _result = self._fallback_dict[x]
        except KeyError:
            _result = {}
        fallback_ = _result

        return Settings(settings_, fallback_)

    def set(self, key, value):
        self._nested_set(self._settings_dict, key.split('.'), value)

    def get(self, setting_key):
        _path = setting_key.split(".")
        _result = self._settings_dict
        for x in _path:
            _result = _result.get(x, {})
        if _result == {}:
            _result = self._fallback_dict
            for x in _path:
                _result = _result.get(x, {})
                if _result == {}:
                    return None
        return _result

    def _nested_set(self, dic, keys, value):
        for key in keys[:-1]:
            dic = dic.setdefault(key, {})
        dic[keys[-1]] = value

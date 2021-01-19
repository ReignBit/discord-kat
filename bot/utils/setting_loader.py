import json
import logging


class Settings:
    """A data class that looks for a value in dict1 before checking dict2."""

    def __init__(self, config_data: dict = None, fallback_data: dict = None):
        self._settings_dict = {}
        self._fallback_dict = {}

        if config_data:
            self._setting_dict = config_data
        if fallback_data:
            self._fallback_dict = fallback_data

    @classmethod
    def from_file(cls, config_file, fallback_file):
        with open(config_file, "r") as f:
            try:
                cls._setting_dict = json.load(f)
            except json.DecodeError:
                cls._setting_dict = {}

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

    def __getitem__(self, key):
        item = self._settings_dict.get(key, None)
        if item is None:
            fallback_item = self._fallback_dict.get(key, None)
            if fallback_item is None:
                return None
            return fallback_item
        return item

    def __setitem__(self, key, value):
        # We shouldn't really be setting values to the config,
        # But the capability is here just in case.
        self._settings_dict[key] = value

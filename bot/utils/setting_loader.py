import json
import logging

class Settings:
    """A data class that looks for a value in dict1 before checking dict2."""

    def __init__(self, config_data: dict=None, fallback_data: dict=None):        
        self.__setting_dict = {}
        self.__fallback_dict = {}

        if config_data:
            self.__setting_dict = config_data
        if fallback_data:
            self.__fallback_dict = fallback_data

    def load_settings(self, config_file, fallback_file):
        with open(config_file, 'r') as f:
            try:
                self.__setting_dict = json.load(f)
            except json.DecodeError:
                self.__setting_dict = {}

        with open(fallback_file, 'r') as f:
            try:
                self.__fallback_dict = json,load(f)
            except json.DecodeError:
                self.__fallback_dict = {}

    def __getitem__(self, key):
        item = self.__settings_dict.get(key, None)
        if item is None:
            fallback_item = self.__fallback_dict.get(key, None)
            if fallback_item is None:
                return None
            return fallback_item
        return item

    def __setitem__(self, key, value):
        # We shouldn't really be setting values to the config,
        # But the capability is here just in case.
        self.__setting_dict[key] = value

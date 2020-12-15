class ConfigSetting:
    """
        Holds information about a command / value that can be modified through Kat's $config command.
        These are normally held in a cog's `config_settings` property, and used in the config cog for easy access to all
        configurable values.

        This might require a slight rework again in how we store these properties database side, but we'll see :)

    """
    def __init__(self, name, value, default, min_max):
        self.name = name
        self.value = value
        self.default = default
        self.min_max = min_max

    @classmethod
    def from_dict(cls, data: dict) -> ConfigSetting:
        """Creates a new ConfigSetting class instance from a dict of params."""
        cls.name = data['name']
        cls.value = data['value']
        cls.default = data['default']
        cls.min_max = data['min_max']
        return cls

    def to_dict(self) -> dict:
        """Returns class in the form of a dict to be used for serialization"""
        return {"name": self.name, "value": self.value, "default": self.default, "min_max": self.min_max}

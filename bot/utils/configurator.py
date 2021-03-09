from typing import Union


class ConfigElementAlreadyExistsException(Exception):
    def __init__(self, name):
        raise Exception("Config element named {} already exists!".format(name))


class ConfigCategory:
    def __init__(self, name, cmd, desc=""):
        self.name = name
        self.cmd = cmd
        self.desc = desc if desc != "" else None

        self._commands = []


class ConfigCommand:
    def __init__(self, category, name, get_value_func, cmd_func):
        self.category = category
        self.name = name
        self.get_value_func = get_value_func
        self.cmd_func = cmd_func


class Config:
    """Config class for KatCogs

    Data class storing information about editable per-guild information,
    for example level experience multipliers, or other cog-specific data.

    This class allows for ease of implementation in cogs, removing the need
    for a seperate config cog in charge of manipulating these variables, and
    automatic creation of embeds and visual elements for discord text channels.

    Allows for the editing of cog settings that are stored on the database, per guild.
    Each cog has an instance of this, if no config elements are created on cog start,
    then the instance is deleted.

    `add_category`; Add a new config category ($config).
    `add_configurable`; Adds a new config element to the passed category.
    `remove_category`; Removes an existing category.
    `remove_configurable`; Removes an existing config element.
    """

    def __init__(self):
        self._categories = []

    def add_category(self, name, cmd, desc="") -> int:
        """Add a new config category and return its id."""
        for category in self._categories:
            if name == category.name:
                raise ConfigElementAlreadyExistsException(name)

        cate = ConfigCategory(name, cmd, desc)
        self._categories.append(cate)
        return len(self._categories) - 1

    def remove_category(self, id: int) -> None:
        """Remove a config category from the config. (Referenced by id)"""
        self._categories[id] = None

    def add_configurable(
        self, category: ConfigCategory, name, get_value_func, cmd_func
    ) -> Union[int, None]:
        if category in self._categories:
            configurable = ConfigCommand(category, name, get_value_func, cmd_func)
            category._commands.append(configurable)
            return len(category._commands) - 1
        return None

    def remove_configurable(self, category, id):
        category._commands[id] = None

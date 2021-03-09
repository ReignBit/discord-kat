import datetime

from discord.ext.commands.converter import Converter


class DateTimeConverter(Converter):
    def __init__(self):
        super().__init__()

    async def convert(self, ctx, arg):
        try:
            return datetime.datetime.strptime(arg, "%d/%m/%y %H:%M")
        except ValueError:
            raise


class TimeConverter(Converter):
    def __init__(self):
        super().__init__()

    async def convert(self, ctx, arg):
        try:
            return datetime.datetime.strptime(arg, "%H:%M")
        except ValueError:
            raise


class DateConverter(Converter):
    def __init__(self):
        super().__init__()

    async def convert(self, ctx, arg):
        try:
            return datetime.datetime.strptime(arg, "%d/%m/%y")
        except ValueError:
            raise

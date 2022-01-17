"""Custom logger for Kat.

Includes Windows and Linux supported terminal colors and writing to log files.
"""
from pathlib import Path
from logging import getLoggerClass, setLoggerClass, addLevelName, NOTSET
import logging
import colorama
import os

from bot.utils.extensions import compress_file
from bot.utils import constants


colorama.init()


def _clean_logs():
    """ Archives the last latest.log and gets it ready for this instance's logging"""
    if "logs" not in os.listdir():
        os.mkdir("logs")

    if "latest.log" in os.listdir("logs"):
        date = ""
        first_line = ""
        # open the latest log file
        with open("logs/latest.log", "r") as f:
            first_line = f.readline()
        # extract the date and time from the first entry (would be approx. boot time)
        date = first_line.split("]")[0][1:]  # DD-MM-YY HH:MM:SS
        date = date.replace(":", "-").replace(" ", "_")

        # TODO: Tidy this up, maybe change where we load the config to avoid loading config twice
        if constants.Logger.compress:
            # take the contents of latest.log and compress them to a new gzip file.
            with open("logs/{}.log.gz".format(date), "wb") as f:
                f.write(compress_file("logs/latest.log"))
        else:
            os.rename("logs/latest.log", "logs/{}.log".format(date))
        # delete latest.log ready for new log
        os.remove("logs/latest.log")

        # remove archived logs that are less than 1024 bytes.
        for f in os.listdir("logs"):
            if f.endswith(".gz") and Path("logs/" + f).stat().st_size < 1024:
                os.remove("logs/" + f)


def get_logger(name):
    setLoggerClass(MyLogger)
    if name == "__main__":
        _clean_logs()
        name = "Kat"

    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        s_handler = logging.StreamHandler()

        f_handler = MyFileHandler('logs/latest.log')
        s_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s", datefmt='%d-%b-%y %H:%M:%S')

        s_handler.setFormatter(CustomFormatter())
        f_handler.setFormatter(fmt)

        logger.addHandler(s_handler)
        logger.addHandler(f_handler)

        logging.addLevelName(12, "READY")

        def ready(self, msg, *args, **kwargs):
            if logger.isEnabledFor(12):
                logger._log(12, msg, args, **kwargs)

        setattr(logger, "connnected", ready)

    return logger


class Color:
    @staticmethod
    def color_test():
        for x in range(0, 91):
            print(f"\033[1;{x}mTest (1:{x})\033[0;0m")

    END = "\033[0;0m"

    # region NORMAL_COLORS
    WHITE = "\033[1;1m"
    # not sure of use case. Impossible to read on black consoles.
    BLACK = "\033[1;30m"
    RED = "\033[1;33m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[1;34m"
    PURPLE = "\033[1;35m"
    AQUA = "\033[1;36m"
    RED_HIGHLIGHT = "\033[1;41m"
    GREEN_HIGHTLIGHT = "\033[1;42m"
    YELLOW_HIGHLIGHT = "\033[1;43m"
    BLUE_HIGHLIGHT = "\033[1;44m"
    PURPLE_HIGHLIGHT = "\033[1;45m"
    AQUA_HIGHLIGHT = "\033[1;46m"
    # again not sure of use case. Impossible to read with white/default text.
    WHITE_HIGHLIGHT = "\033[1;47m"
    GREY = "\033[1;90m"             # english spelling
    GRAY = "\033[1;90m"             # american spelling
    # endregion

    # region DARK_COLORS
    DARK_RED = "\033[0;31m"
    DARK_GREEN = "\033[0;32m"
    DARK_YELLOW = "\033[0;33m"
    DARK_BLUE = "\033[0;34m"
    DARK_PURPLE = "\033[0;35m"
    DARK_AQUA = "\033[0;36m"
    DARK_RED_HIGHLIGHT = "\033[0;41m"
    DARK_GREEN_HIGHTLIGHT = "\033[0;42m"
    DARK_YELLOW_HIGHLIGHT = "\033[0;43m"
    DARK_BLUE_HIGHLIGHT = "\033[0;44m"
    DARK_PURPLE_HIGHLIGHT = "\033[0;45m"
    DARK_AQUA_HIGHLIGHT = "\033[0;46m"
    # again not sure of use case. Impossible to read with white/default text.
    DARK_WHITE_HIGHLIGHT = "\033[0;47m"
    # endregion


READY = 12


class MyFileHandler(logging.Handler):
    def __init__(self, filename):
        self.filename = filename
        super().__init__()

    def emit(self, record):
        log_text = self.format(record)
        try:
            fh = open(self.filename, "a", encoding="utf-8")
            fh.write(log_text + "\n")
            fh.close()

            return True
        except IOError:
            return False


class MyLogger(getLoggerClass()):
    def __init__(self, name, level=NOTSET):
        super().__init__(name, level)

        addLevelName(READY, "READY")

    def ready(self, msg, *args, **kwargs):
        if self.isEnabledFor(READY):
            self._log(READY, msg, args, **kwargs)

    def destroy(self):
        for handler in self.handlers[:]:
            logging.getLogger(self.name).removeHandler(handler)


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = Color.GRAY
    aqua = Color.AQUA
    yellow = Color.YELLOW
    red = Color.RED
    bold_red = Color.DARK_RED
    reset = Color.END
    fmt = " [%(name)s] : %(message)s"

    FORMATS = {
        logging.DEBUG: f"{aqua}[%(asctime)s] [DBUG]{fmt}(%(filename)s:%(lineno)d){reset}",
        logging.INFO: f"{grey}[%(asctime)s] [%(levelname)s]{fmt}{reset}",
        logging.WARNING: f"{yellow}[%(asctime)s] [WARN]{fmt}(%(filename)s:%(lineno)d){reset}",
        logging.ERROR: f"{red}[%(asctime)s] [EXCP]{fmt}(%(filename)s:%(lineno)d){reset}",
        logging.CRITICAL: f"{bold_red}[%(asctime)s] [CRIT]{fmt}(%(filename)s:%(lineno)d){reset}",
        READY: Color.GREEN + fmt + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%d-%b-%y %H:%M:%S')
        return formatter.format(record)

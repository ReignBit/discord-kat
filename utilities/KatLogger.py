import logging
import colorama
import os
import sys

colorama.init()

def get_logger(name):
    logging.setLoggerClass(MyLogger)
    if name == "__main__": name = "Kat"

    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        s_handler = logging.StreamHandler()

        # TODO: Move filepath to config

        f_handler = MyFileHandler('logs/latest.log')
        s_handler.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.DEBUG)

        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s", datefmt='%d-%b-%y %H:%M:%S')

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
        for x in range(0,91):
            print(f"\033[1;{x}mTest (1:{x})\033[0;0m")

    END = "\033[0;0m"

    # region NORMAL_COLORS
    WHITE = "\033[1;1m"
    BLACK = "\033[1;30m"            # not sure of use case. Impossible to read on black consoles.
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
    WHITE_HIGHLIGHT = "\033[1;47m"  # again not sure of use case. Impossible to read with white/default text.
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
    DARK_WHITE_HIGHLIGHT = "\033[0;47m"  # again not sure of use case. Impossible to read with white/default text.
    # endregion




from logging import getLoggerClass, addLevelName, setLoggerClass, NOTSET
READY = 12


class MyFileHandler(logging.Handler):
    def __init__(self, filename):
        self.filename = filename
        super().__init__()

    def emit(self, record):
        log_text = self.format(record)
        try:
            fh = open(self.filename, "a")
            fh.write(log_text + "\n")
            fh.close()

            return True
        except:
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
        logging.DEBUG: aqua + "[%(asctime)s] [DBUG]" + fmt + "(%(filename)s:%(lineno)d)" + reset,
        logging.INFO: grey + "[%(asctime)s] [%(levelname)s]" + fmt + reset,
        logging.WARNING: yellow + "[%(asctime)s] [WARN]" + fmt + "(%(filename)s:%(lineno)d)" + reset,
        logging.ERROR: red + "[%(asctime)s] [EXCP]" + fmt + "(%(filename)s:%(lineno)d)" + reset,
        logging.CRITICAL: bold_red + "[%(asctime)s] [CRIT]" + fmt + "(%(filename)s:%(lineno)d)" + reset,
        READY: Color.GREEN + fmt + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%d-%b-%y %H:%M:%S')
        return formatter.format(record)
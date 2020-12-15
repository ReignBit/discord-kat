"""Common color codes to be used in log decoration on both Windows and Linux."""


END = "\033[0;0m"

# region NORMAL_COLORS
WHITE = "\033[1;1m"
# not sure of use case. Impossible to read on black consoles.
BLACK = "\033[1;30m"
RED = "\033[1;31m"
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
GREY = "\033[1;90m"  # english spelling
GRAY = "\033[1;90m"  # american spelling

# DARK_COLORS
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

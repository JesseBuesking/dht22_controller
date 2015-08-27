from bbds import config
from termcolor import colored as c


try:
    from colorama import init
    # supposedly "improves/fixes" colors on windows
    init()
except:
    pass


__all__ = [
    'colored'
]

# these colors don't appear to work on windows, so swap for the value specified
windows_color_swap = {
    'grey': 'white'
}

def colored(value, color, *args, **kwargs):
    if config.ISWINDOWS: color = windows_color_swap.get(color, color)
    return c(value, color, *args, **kwargs)

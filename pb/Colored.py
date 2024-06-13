"""
Provide ANSI escape codes for beautiful output.
"""

class Esc:
    """Class containing ANSI escape codes"""
    bell = "\a"
    reset = "\033[0m"
    bold = "\033[1m"
    n_bold = "\033[22m"
    dim = "\033[2m"
    n_dim = "\033[22m"
    red = "\033[31m"
    green = "\033[32m"
    default = "\033[39m"
    red_bright = "\033[91m"
    green_bright = "\033[92m"

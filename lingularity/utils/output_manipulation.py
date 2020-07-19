import os
import sys
import platform


def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    [erase_previous_line() for _ in range(n_lines)]

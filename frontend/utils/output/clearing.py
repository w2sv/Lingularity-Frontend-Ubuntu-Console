import subprocess
import sys
import platform


_CLEAR_COMMAND = ['clear', 'cls'][platform.system() == 'Windows']


def clear_screen():
    subprocess.run([_CLEAR_COMMAND])


def _erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    print('')
    for _ in range(n_lines + 1):
        _erase_previous_line()

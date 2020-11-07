import subprocess
import sys
import platform


def clear_screen():
    subprocess.run(['clear', 'cls'][platform.system() == 'Windows'], shell=True)


def _erase_previous_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def erase_lines(n_lines: int):
    print('')
    for _ in range(n_lines + 1):
        _erase_previous_line()

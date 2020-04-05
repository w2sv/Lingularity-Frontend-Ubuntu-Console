from abc import ABC, abstractmethod
import os
import platform
import sys


class Trainer(ABC):
    @staticmethod
    def clear_screen():
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    @staticmethod
    def erase_previous_line():
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

    @abstractmethod
    def run(self):
        pass

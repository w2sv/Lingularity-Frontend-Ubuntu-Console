from typing import Callable
from enum import Enum, auto


class ReentryPoint(Enum):
    Login = auto()
    LanguageAddition = auto()
    Home = auto()
    TrainingSelection = auto()
    Exit = auto()


ReentryPointProvider = Callable[[], ReentryPoint]

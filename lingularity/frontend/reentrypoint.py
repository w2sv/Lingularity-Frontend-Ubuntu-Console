from enum import Enum, auto


class ReentryPoint(Enum):
    Login = auto()
    LanguageAddition = auto()
    LanguageSelection = auto()
    TrainingSelection = auto()
    Exit = auto()

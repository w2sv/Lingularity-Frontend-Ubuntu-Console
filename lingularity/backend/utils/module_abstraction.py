import sys
from typing import *
from functools import partial
from types import ModuleType


def abstractmodulemethod(function: Callable):
    calling_module = sys.modules[function.__module__]
    _is_calling_module_package_module = partial(_is_package_module, package_name=calling_module.__package__)

    for _, package_module in filter(lambda item: _is_calling_module_package_module(*item), calling_module.__dict__.items()):
        if function.__name__ not in dir(package_module) or not hasattr(package_module.__dict__[function.__name__], '__call__'):
            raise NotImplementedError(f"Can't initialize module {calling_module} with abstractmodulemethod {function.__name__}")


def _is_package_module(module_name: str, module: ModuleType, package_name: str) -> bool:
    return not _is_dunder(module_name) and _is_module(module) and module.__package__ == package_name


def _is_dunder(name: str) -> bool:
    return name.startswith('__') and name.endswith('__')


def _is_module(module_candidate: object) -> bool:
    return module_candidate.__class__.__name__ == 'module'

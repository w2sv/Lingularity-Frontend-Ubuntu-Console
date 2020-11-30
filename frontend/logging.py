from backend.logging import enable_backend_logging as _enable_backend_logging
import os


def enable_backend_logging():
    _enable_backend_logging(file_path=f'{os.getcwd()}/logging.txt')

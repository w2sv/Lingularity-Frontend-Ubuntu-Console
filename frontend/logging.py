from backend.logging import enable_backend_logging
import os


enable_backend_logging(file_path=f'{os.getcwd()}/logging.txt')

from typing import Optional
import os

from frontend.utils import fernet


USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'


def retrieve() -> Optional[str]:
    if not os.path.exists(USER_ENCRYPTION_FILE_PATH):
        return None
    return fernet.decrypt(open(USER_ENCRYPTION_FILE_PATH, 'rb').read())


def store(username: str):
    with open(USER_ENCRYPTION_FILE_PATH, 'wb+') as user_encryption_file:
        user_encryption_file.write(fernet.encrypt(username))


def remove():
    os.remove(USER_ENCRYPTION_FILE_PATH)

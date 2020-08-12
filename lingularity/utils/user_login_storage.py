from typing import Optional
import os

from cryptography.fernet import Fernet

_FERNET_KEY_FILE_PATH = f'{os.getcwd()}/.fernet_key'


def fernet_key_existent() -> bool:
    return os.path.exists(_FERNET_KEY_FILE_PATH)


def write_fernet_key():
    key = Fernet.generate_key()
    with open(_FERNET_KEY_FILE_PATH, 'wb') as key_file:
        key_file.write(key)


def write_fernet_key_if_not_existent():
    if not fernet_key_existent():
        write_fernet_key()


def _load_fernet_key() -> str:
    return open(_FERNET_KEY_FILE_PATH, "rb").read()


def encrypt(message: str,) -> str:
    return Fernet(key=_load_fernet_key()).encrypt(message.encode())


def decrypt(encrypted_message: str) -> str:
    return Fernet(key=_load_fernet_key()).decrypt(encrypted_message).decode('ascii')


USER_ENCRYPTION_FILE_PATH = f'{os.getcwd()}/.logged_in_user'


def get_logged_in_user() -> Optional[str]:
    if not os.path.exists(USER_ENCRYPTION_FILE_PATH):
        return None

    return decrypt(open(USER_ENCRYPTION_FILE_PATH, 'rb').read())


def store_user_login(username: str):
    with open(USER_ENCRYPTION_FILE_PATH, 'wb+') as user_encryption_file:
        user_encryption_file.write(encrypt(username))


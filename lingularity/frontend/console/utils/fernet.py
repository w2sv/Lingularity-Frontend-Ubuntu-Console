import os

from cryptography.fernet import Fernet


_KEY_FILE_PATH = f'{os.getcwd()}/.fernet_key'


def key_existent() -> bool:
    return os.path.exists(_KEY_FILE_PATH)


def write_key():
    key = Fernet.generate_key()
    with open(_KEY_FILE_PATH, 'wb') as key_file:
        key_file.write(key)


def encrypt(message: str,) -> bytes:
    return Fernet(key=_load_key()).encrypt(message.encode())


def decrypt(encrypted_message: bytes) -> str:
    return Fernet(key=_load_key()).decrypt(encrypted_message).decode('ascii')


def _load_key() -> bytes:
    return open(_KEY_FILE_PATH, "rb").read()

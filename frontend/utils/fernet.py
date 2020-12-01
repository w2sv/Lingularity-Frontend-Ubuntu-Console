import os

from cryptography.fernet import Fernet


def encrypt(message: str,) -> bytes:
    return Fernet(key=_load_key()).encrypt(message.encode())


def decrypt(encrypted_message: bytes) -> str:
    return Fernet(key=_load_key()).decrypt(encrypted_message).decode('ascii')


# ---------------
# Key
# ---------------
_KEY_FILE_PATH = f'{os.getcwd()}/.keys/fernet'


def _key_existent() -> bool:
    return os.path.exists(_KEY_FILE_PATH)


def _write_key():
    key = Fernet.generate_key()
    with open(_KEY_FILE_PATH, 'wb') as key_file:
        key_file.write(key)


if not _key_existent():
    _write_key()


def _load_key() -> bytes:
    return open(_KEY_FILE_PATH, "rb").read()

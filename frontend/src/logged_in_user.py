from typing import Optional

from frontend.src.paths import KEYS_DIR_PATH
from frontend.src.utils import fernet


_user_encryption_fp = KEYS_DIR_PATH / 'user'


def retrieve() -> Optional[str]:
    try:
        with open(_user_encryption_fp, 'rb') as f:
            return fernet.decrypt(f.read())
    except FileNotFoundError:
        return None


def store(username: str):
    with open(_user_encryption_fp, 'wb+') as f:
        f.write(fernet.encrypt(username))


def remove():
    _user_encryption_fp.unlink()

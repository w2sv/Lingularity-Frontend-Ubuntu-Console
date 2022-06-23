from typing import Optional

from frontend import key_dir_path
from frontend.utils import fernet


_user_encryption_fp = key_dir_path / 'user'


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

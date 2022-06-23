from pathlib import Path
from typing import Optional

from frontend.utils import fernet


_user_encryption_fp = Path().cwd() / '.keys' / 'user'


def retrieve() -> Optional[str]:
    try:
        with open(_user_encryption_fp, 'rb') as f:
            return fernet.decrypt(f.read())
    except FileNotFoundError:
        return None


def store(username: str):
    with open(_user_encryption_fp, 'wb+') as user_encryption_file:
        user_encryption_file.write(fernet.encrypt(username))


def remove():
    _user_encryption_fp.unlink()

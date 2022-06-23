from cryptography.fernet import Fernet

from frontend import key_dir_path


_key_fp = key_dir_path / 'fernet'


def encrypt(message: str) -> bytes:
    if not _key_fp.exists():
        _write_generated_key()
    return Fernet(key=_load_key()).encrypt(message.encode())


def decrypt(encrypted_message: bytes) -> str:
    return Fernet(key=_load_key()).decrypt(encrypted_message).decode('ascii')


# ---------------
# Key IO
# ---------------

def _write_generated_key():
    with open(_key_fp, 'wb') as f:
        f.write(Fernet.generate_key())


def _load_key() -> bytes:
    return open(_key_fp, 'rb').read()

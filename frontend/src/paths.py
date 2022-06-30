from pathlib import Path


KEYS_DIR_PATH = Path().cwd() / '.keys'

_PACKAGE_ROOT = Path(__file__).parent.parent

DATA_DIR_PATH = _PACKAGE_ROOT / 'data'
RESOURCE_DIR_PATH = _PACKAGE_ROOT / 'resources'
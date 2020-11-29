import subprocess


def set_title(title: str):
    # TODO: fix on ubuntu 20.04

    subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-N', f'"Lingularity - {title}"'])


DEFAULT_TITLE = 'Acquire Languages the Litboy Way'

def invalid_mailadress(mailadress: str) -> bool:
    return '@' not in mailadress or mailadress.strip().__len__() < 3


def invalid_username(username: str) -> bool:
    return not bool(len(username.strip()))


def invalid_password(password: str) -> bool:
    return len(password) < 5
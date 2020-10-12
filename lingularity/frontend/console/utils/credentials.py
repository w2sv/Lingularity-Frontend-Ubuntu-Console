def invalid_mailaddress(mailaddress: str) -> bool:
    MIN_MAILADDRESS_LENGTH = 3

    return '@' not in mailaddress or len(mailaddress.strip()) < MIN_MAILADDRESS_LENGTH


def invalid_username(username: str) -> bool:
    return not bool(len(username.strip()))


def invalid_password(password: str) -> bool:
    MIN_PASSWORD_LENGTH = 5

    return len(password) < MIN_PASSWORD_LENGTH

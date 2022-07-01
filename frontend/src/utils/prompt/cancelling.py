from pynput import keyboard


QUERY_CANCELLED = '{QUERY_CANCELLED}'


def _cancelable(prompt: str) -> str:
    print(prompt, end='', flush=True)

    if _escape_key_pressed():
        return QUERY_CANCELLED

    return _escape_unicode_stripped(input(''))


def _escape_key_pressed() -> bool:
    pressed_key = None

    def on_press(key):
        nonlocal pressed_key
        pressed_key = key
        return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return pressed_key == keyboard.Key.esc


def _escape_unicode_stripped(string: str) -> str:
    return string.replace('', '')

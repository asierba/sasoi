from collections.abc import Mapping


class SettingError(Exception):
    pass


def required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise SettingError(f"{name} is not set")
    return value

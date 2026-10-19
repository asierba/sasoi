from getpass import getpass

from garminconnect import Garmin

TOKENSTORE = "~/.garminconnect"


def login() -> Garmin:
    try:
        garmin = Garmin()
        garmin.login(TOKENSTORE)
    except Exception:
        garmin = Garmin(input("Garmin email: "), getpass("Garmin password: "), prompt_mfa=lambda: input("MFA code: "))
        garmin.login(TOKENSTORE)
    return garmin

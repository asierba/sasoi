from getpass import getpass

from garminconnect import Garmin, GarminConnectAuthenticationError

TOKENSTORE = "~/.garminconnect"


def login() -> Garmin:
    try:
        garmin = Garmin()
        garmin.login(TOKENSTORE)
    except GarminConnectAuthenticationError:
        garmin = Garmin(input("Garmin email: "), getpass("Garmin password: "), prompt_mfa=lambda: input("MFA code: "))
        garmin.login(TOKENSTORE)
    return garmin

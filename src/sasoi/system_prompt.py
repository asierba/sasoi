from datetime import date


def system_prompt() -> str:
    today = date.today()
    return f"Today is {today:%A}, {today.isoformat()}."

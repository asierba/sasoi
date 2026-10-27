from datetime import date


def system_prompt(athlete_profile: str) -> str:
    today = date.today()
    return (
        f"Today is {today:%A}, {today.isoformat()}.\n\n"
        f"<athlete_profile>\n{athlete_profile.strip()}\n</athlete_profile>\n\n"
        "Every recommendation must fit the athlete profile, including its weekly session budget."
    )

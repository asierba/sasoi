import time_machine

from sasoi.system_prompt import system_prompt


class TestSystemPrompt:
    @time_machine.travel("2026-10-20 09:00")
    def test_states_todays_weekday_and_date_and_the_athlete_profile(self):
        assert system_prompt("Up to 3 sessions a week.\n") == (
            "Today is Tuesday, 2026-10-20.\n\n"
            "<athlete_profile>\nUp to 3 sessions a week.\n</athlete_profile>\n\n"
            "Every recommendation must fit the athlete profile, including its weekly session budget."
        )

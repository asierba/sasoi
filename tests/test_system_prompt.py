import time_machine

from sasoi.system_prompt import system_prompt


class TestSystemPrompt:
    @time_machine.travel("2026-10-20 09:00")
    def test_states_todays_weekday_and_date(self):
        assert system_prompt() == "Today is Tuesday, 2026-10-20."

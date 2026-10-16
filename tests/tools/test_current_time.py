from datetime import datetime

from sasoi.tools.current_time import current_time


class TestCurrentTime:
    def test_returns_now_with_timezone(self):
        before = datetime.now().astimezone().replace(microsecond=0)

        now = datetime.fromisoformat(current_time.run({}))

        after = datetime.now().astimezone()
        assert before <= now <= after

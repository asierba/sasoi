from datetime import datetime

from sasoi.tools.current_time import current_time


def test_current_time_returns_now_with_timezone():
    before = datetime.now().astimezone().replace(microsecond=0)

    now = datetime.fromisoformat(current_time.run({}))

    after = datetime.now().astimezone()
    assert before <= now <= after

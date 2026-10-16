import pytest

from sasoi.claude_client import ClaudeApiError
from sasoi.cli import DEFAULT_MODEL, RED, RESET, YELLOW, Config, load_config, repl


class FakeAgent:
    def __init__(self, *answers: str | BaseException):
        self._answers = list(answers)
        self.prompts: list[str] = []

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        answer = self._answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer


def typed(*lines: str):
    pending = list(lines)

    def read(prompt: str) -> str:
        if not pending:
            raise EOFError
        return pending.pop(0)

    return read


class TestRepl:
    def test_writes_each_answer(self):
        agent = FakeAgent("Hi!", "You said hello")
        written: list[str] = []

        repl(agent, read=typed("hello", "what did I say?"), write=written.append)

        assert agent.prompts == ["hello", "what did I say?"]
        assert written == ["Hi!", "You said hello"]

    def test_skips_empty_prompts(self):
        agent = FakeAgent()

        repl(agent, read=typed("   ", ""), write=lambda text: None)

        assert agent.prompts == []

    def test_shows_api_error_in_red_and_keeps_going(self):
        agent = FakeAgent(ClaudeApiError(529, "overloaded_error", "Overloaded"), "second reply")
        written: list[str] = []

        repl(agent, read=typed("first", "second"), write=written.append)

        assert written == [f"{RED}Error: 529 overloaded_error: Overloaded{RESET}", "second reply"]

    def test_shows_interrupted_in_yellow_on_ctrl_c_and_keeps_going(self):
        agent = FakeAgent(KeyboardInterrupt(), "second reply")
        written: list[str] = []

        repl(agent, read=typed("first", "second"), write=written.append)

        assert written == [f"{YELLOW}Interrupted{RESET}", "second reply"]


class TestLoadConfig:
    def test_exits_with_message_when_api_key_missing(self):
        with pytest.raises(SystemExit) as raised:
            load_config({})

        assert raised.value.code == f"{RED}Error: ANTHROPIC_API_KEY is not set{RESET}"

    def test_uses_default_model_when_not_set(self):
        assert load_config({"ANTHROPIC_API_KEY": "key"}) == Config("key", DEFAULT_MODEL)

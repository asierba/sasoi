import pytest

from sasoi.agent import Answer
from sasoi.claude_client import ClaudeApiError, Usage
from sasoi.cli import DIM, RED, RESET, YELLOW, Config, load_config, repl
from sasoi.pricing import Price

A_USAGE = Usage(input_tokens=1, output_tokens=1)
A_PROMPT = "a prompt"
AN_ANSWER_TEXT = "an answer"
AN_API_KEY = "an api key"
A_MODEL = "a model"


def an_answer(text: str) -> Answer:
    return Answer(text, A_USAGE)


class FakeAgent:
    def __init__(self, *answers: Answer | BaseException):
        self._answers = list(answers)
        self.prompts: list[str] = []

    def ask(self, prompt: str) -> Answer:
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
        agent = FakeAgent(an_answer("Hi!"), an_answer("You said hello"))
        written: list[str] = []

        repl(agent, read=typed("hello", "what did I say?"), write=written.append)

        assert agent.prompts == ["hello", "what did I say?"]
        [first_answer, _, second_answer, _] = written
        assert [first_answer, second_answer] == ["Hi!", "You said hello"]

    def test_writes_tokens_and_cost_after_each_answer(self):
        agent = FakeAgent(Answer("Hi!", Usage(input_tokens=1_200, output_tokens=300)))
        written: list[str] = []

        repl(agent, Price(input_per_mtok=1.00, output_per_mtok=5.00), read=typed(A_PROMPT), write=written.append)

        assert written == ["Hi!", f"{DIM}1,200 in · 300 out · $0.0027{RESET}"]

    def test_writes_tokens_only_when_model_has_no_price(self):
        agent = FakeAgent(Answer(AN_ANSWER_TEXT, Usage(input_tokens=1_200, output_tokens=300)))
        written: list[str] = []

        repl(agent, None, read=typed(A_PROMPT), write=written.append)

        [_, usage_line] = written
        assert usage_line == f"{DIM}1,200 in · 300 out{RESET}"

    def test_skips_empty_prompts(self):
        agent = FakeAgent()

        repl(agent, read=typed("   ", ""), write=lambda text: None)

        assert agent.prompts == []

    def test_shows_api_error_in_red_and_keeps_going(self):
        agent = FakeAgent(ClaudeApiError(529, "overloaded_error", "Overloaded"), an_answer("second reply"))
        written: list[str] = []

        repl(agent, read=typed(A_PROMPT, A_PROMPT), write=written.append)

        [error, second_answer, _] = written
        assert [error, second_answer] == [f"{RED}Error: 529 overloaded_error: Overloaded{RESET}", "second reply"]

    def test_shows_interrupted_in_yellow_on_ctrl_c_and_keeps_going(self):
        agent = FakeAgent(KeyboardInterrupt(), an_answer("second reply"))
        written: list[str] = []

        repl(agent, read=typed(A_PROMPT, A_PROMPT), write=written.append)

        [interrupted, second_answer, _] = written
        assert [interrupted, second_answer] == [f"{YELLOW}Interrupted{RESET}", "second reply"]


class TestLoadConfig:
    def test_exits_with_message_when_api_key_missing(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"SASOI_MODEL": A_MODEL})

        assert raised.value.code == f"{RED}Error: ANTHROPIC_API_KEY is not set{RESET}"

    def test_exits_with_message_when_model_missing(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"ANTHROPIC_API_KEY": AN_API_KEY})

        assert raised.value.code == f"{RED}Error: SASOI_MODEL is not set{RESET}"

    def test_reads_api_key_and_model(self):
        assert load_config({"ANTHROPIC_API_KEY": "key", "SASOI_MODEL": "claude-test"}) == Config("key", "claude-test")

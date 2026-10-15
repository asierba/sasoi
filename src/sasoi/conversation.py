class Conversation:
    def __init__(self):
        self._messages: list[dict] = []

    def add_user_message(self, text: str) -> None:
        self._messages.append({"role": "user", "content": text})

    def add_assistant_message(self, content: list[dict]) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def add_tool_results(self, results: list[dict]) -> None:
        self._messages.append({"role": "user", "content": results})

    @property
    def messages(self) -> list[dict]:
        return list(self._messages)

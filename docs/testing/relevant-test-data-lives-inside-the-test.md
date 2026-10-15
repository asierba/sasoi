# Testing: Relevant test data lives inside the test

## Convention

Every value that drives the behaviour under test or appears in the assertion is written inside the test body. A value the code requires but the test does not care about goes in a constant prefixed with `A_` or `AN_`, defined next to the tests that use it.

## Benefits

- A test reads top to bottom without scrolling elsewhere in the file.
- The reader sees at once which inputs explain the expected result.
- The `A_` prefix states that any value would do, so the reader can skip it.

## Examples

### Good: relevant values inline, irrelevant value named as any

```python
A_STOP_REASON = "end_turn"


def test_reply_returns_text():
    reply = Reply([{"type": "text", "text": "Hello"}], A_STOP_REASON)

    assert reply.text == "Hello"
```

### Good: the block to ignore reduced to its type

```python
def test_reply_text_ignores_non_text_blocks():
    reply = Reply([{"type": "text", "text": "Let me check"}, {"type": "tool_use"}], A_STOP_REASON)

    assert reply.text == "Let me check"
```

### Bad: asserted values defined away from the test

```python
TEXT_BLOCK = {"type": "text", "text": "Let me check the time"}
TOOL_USE_BLOCK = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}


def test_reply_text_ignores_non_text_blocks():
    reply = Reply([TEXT_BLOCK, TOOL_USE_BLOCK], "tool_use")

    assert reply.text == "Let me check the time"
```

### Bad: required but irrelevant value looks meaningful

```python
def test_reply_returns_text():
    reply = Reply([{"type": "text", "text": "Hello"}], "end_turn")

    assert reply.text == "Hello"
```

### Bad: setup unrelated to the assertion

```python
def test_send_posts_prompt_and_returns_text():
    tools = [{"name": "current_time", "description": "Now", "input_schema": {"type": "object"}}]

    reply = client.send([{"role": "user", "content": "hi"}], tools)

    assert reply.text == "Hello there"
```

## Real world examples

- [`Reply` tests and `A_STOP_REASON`](../../tests/test_claude_client.py).
- [`text_reply`, `FakeClient` and `typed` helpers](../../tests/test_cli.py).

## Exceptional cases: When to not take into account this convention

- Helpers and fixtures that do not affect the assertion, such as fake clients or reply builders, may live elsewhere in the file.

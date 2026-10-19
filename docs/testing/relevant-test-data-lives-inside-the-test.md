# Testing: Relevant test data lives inside the test

## Convention

Every value that drives the behaviour under test or appears in the assertion is written inside the test body. A value the code requires but the test does not care about goes in a constant prefixed with `A_` or `AN_`, defined next to the tests that use it. A function that builds test data is prefixed with `a_` or `an_` and takes the relevant values as arguments, so they stay visible at the call site.

## Benefits

- A test reads top to bottom without scrolling elsewhere in the file.
- The reader sees at once which inputs explain the expected result.
- The `A_` prefix states that any value would do, so the reader can skip it.
- The `a_` prefix on a builder reads as a sentence and states that only its arguments matter.

## Examples

### Good: relevant values inline, irrelevant value named as any

```python
A_STOP_REASON = "end_turn"


class TestReply:
    def test_returns_text(self):
        reply = Reply([{"type": "text", "text": "Hello"}], A_STOP_REASON)

        assert reply.text == "Hello"
```

### Good: the block to ignore reduced to its type

```python
class TestReply:
    def test_text_ignores_non_text_blocks(self):
        reply = Reply([{"type": "text", "text": "Let me check"}, {"type": "tool_use"}], A_STOP_REASON)

        assert reply.text == "Let me check"
```

### Good: builder named as any, relevant values passed in

```python
def an_activity(activity_id: int, type_key: str) -> dict:
    return {"activityId": activity_id, "activityType": {"typeKey": type_key}}


class TestGarminSource:
    def test_recent_runs_returns_only_runs(self):
        api = FakeGarminApi([an_activity(2, "running"), an_activity(1, "cycling")])

        assert GarminSource(api).recent_runs(10) == [an_activity(2, "running")]
```

### Bad: builder named like a domain function

```python
def activity(activity_id: int, type_key: str) -> dict:
    return {"activityId": activity_id, "activityType": {"typeKey": type_key}}
```

### Bad: asserted values defined away from the test

```python
TEXT_BLOCK = {"type": "text", "text": "Let me check the time"}
TOOL_USE_BLOCK = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}


class TestReply:
    def test_text_ignores_non_text_blocks(self):
        reply = Reply([TEXT_BLOCK, TOOL_USE_BLOCK], "tool_use")

        assert reply.text == "Let me check the time"
```

### Bad: required but irrelevant value looks meaningful

```python
class TestReply:
    def test_returns_text(self):
        reply = Reply([{"type": "text", "text": "Hello"}], "end_turn")

        assert reply.text == "Hello"
```

### Bad: setup unrelated to the assertion

```python
class TestClaudeClient:
    def test_send_posts_prompt_and_returns_text(self):
        tools = [{"name": "current_time", "description": "Now", "input_schema": {"type": "object"}}]

        reply = client.send([{"role": "user", "content": "hi"}], tools)

        assert reply.text == "Hello there"
```

## Real world examples

- [`Reply` tests and `A_STOP_REASON`](../../tests/test_claude_client.py).
- [`a_text_reply` builder and `FakeClient`](../../tests/test_agent.py).
- [`typed` helper](../../tests/test_cli.py).
- [`an_activity` builder](../../tests/ingest/test_garmin_source.py).

## Exceptional cases: When to not take into account this convention

- Helpers and fixtures that do not affect the assertion, such as fake clients or reply builders, may live elsewhere in the file.

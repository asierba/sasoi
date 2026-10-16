# Testing: Assertions state exactly what the test claims

## Convention

An assertion makes every claim of the test visible and checks nothing beyond it. Compare the whole structure when every field is part of the claim; otherwise state the shape explicitly and assert only the relevant fields.

## Benefits

- The reader sees the full claim without inferring hidden assumptions.
- A test fails only when its own claim breaks, not when an unrelated field changes.
- Wrong shapes, such as missing or extra items, fail loudly instead of passing silently.

## Examples

### Good: whole structure compared when every field is the claim

```python
def test_records_request_reply_and_duration(self):
    ...

    assert recorded(sink) == [
        {
            "type": "claude_call",
            "messages": [{"role": "user", "content": "hello"}],
            "tools": [{"name": "current_time"}],
            "content": [{"type": "text", "text": "Hi!"}],
            "stop_reason": "end_turn",
            "duration_ms": 250.0,
        }
    ]
```

### Good: shape stated explicitly, only the relevant field asserted

```python
def test_records_error_and_reraises(self):
    ...

    [event] = recorded(sink)
    assert event["error"] == "529 overloaded_error: Overloaded"
```

### Bad: indexing hides the shape

```python
def test_records_error_and_reraises(self):
    ...

    assert recorded(sink)[0]["error"] == "529 overloaded_error: Overloaded"
```

### Bad: whole structure asserted when the test is about one field

```python
def test_records_error_and_reraises(self):
    ...

    assert recorded(sink) == [
        {
            "type": "claude_call",
            "messages": [{"role": "user", "content": "hello"}],
            "error": "529 overloaded_error: Overloaded",
            "duration_ms": 0.0,
        }
    ]
```

## Real world examples

- [`TestTracedClient` and `TestTracedToolbox`](../../tests/test_tracing.py).

## Related agreements

- [Testing: Relevant test data lives inside the test](./relevant-test-data-lives-inside-the-test.md).

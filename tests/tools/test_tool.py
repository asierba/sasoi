from sasoi.tools.tool import Tool


def test_tool_exposes_definition_and_runs_with_input():
    tool = Tool("echo", "Echo input", {"type": "object"}, lambda tool_input: f"got {tool_input['text']}")

    assert tool.definition == {
        "name": "echo",
        "description": "Echo input",
        "input_schema": {"type": "object"},
    }
    assert tool.run({"text": "hi"}) == "got hi"

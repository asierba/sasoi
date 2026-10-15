from sasoi.tools.tool import Tool, ToolError
from sasoi.tools.toolbox import Toolbox


def test_definitions_lists_every_tool():
    clock = Tool("current_time", "Now", {"type": "object"}, lambda _: "")
    calculator = Tool("calculator", "Evaluate", {"type": "object"}, lambda _: "")

    assert Toolbox([clock, calculator]).definitions == [
        {"name": "current_time", "description": "Now", "input_schema": {"type": "object"}},
        {"name": "calculator", "description": "Evaluate", "input_schema": {"type": "object"}},
    ]


A_DESCRIPTION = "Does something"
AN_INPUT_SCHEMA = {"type": "object"}


def test_run_calls_requested_tool_with_its_input_and_returns_tool_result():
    calculator = Tool(
        "calculator", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda tool_input: f"result of {tool_input['expression']}"
    )
    call = {"id": "toolu_1", "name": "calculator", "input": {"expression": "1 + 1"}}

    assert Toolbox([calculator]).run(call) == {
        "type": "tool_result",
        "tool_use_id": "toolu_1",
        "content": "result of 1 + 1",
    }


def test_run_returns_error_result_when_tool_fails():
    def fail(_: dict) -> str:
        raise ToolError("No place found for 'xqzzqx'")

    geocode = Tool("geocode", A_DESCRIPTION, AN_INPUT_SCHEMA, fail)
    call = {"id": "toolu_1", "name": "geocode", "input": {"place": "xqzzqx"}}

    assert Toolbox([geocode]).run(call) == {
        "type": "tool_result",
        "tool_use_id": "toolu_1",
        "content": "No place found for 'xqzzqx'",
        "is_error": True,
    }

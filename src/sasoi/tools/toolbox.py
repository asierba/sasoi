from sasoi.tools.tool import Tool, ToolError


class Toolbox:
    def __init__(self, tools: list[Tool]):
        self._tools_by_name = {tool.name: tool for tool in tools}

    @property
    def definitions(self) -> list[dict]:
        return [tool.definition for tool in self._tools_by_name.values()]

    def run(self, call: dict) -> dict:
        tool = self._tools_by_name[call["name"]]
        try:
            return {"type": "tool_result", "tool_use_id": call["id"], "content": tool.run(call["input"])}
        except ToolError as error:
            return {"type": "tool_result", "tool_use_id": call["id"], "content": str(error), "is_error": True}

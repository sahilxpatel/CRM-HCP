from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    intent: str
    tool_result: Any
    response: str

import json

from langgraph.graph import END, StateGraph

from app.langgraph.prompts import GENERAL_CHAT_PROMPT, INTENT_PROMPT, RESPONSE_PROMPT
from app.langgraph.state import AgentState
from app.langgraph.tools import AgentTools
from app.langgraph.utils import extract_json
from app.services.groq_client import GroqClient


def build_agent(db):
    llm = GroqClient()
    tools = AgentTools(llm, db)

    def detect_intent(state: AgentState) -> AgentState:
        user_text = state.get("user_input", "")
        messages = [
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": user_text},
        ]
        intent = None
        try:
            raw = llm.complete_text(messages, temperature=0, max_tokens=60)
            parsed = extract_json(raw) or {}
            intent = parsed.get("intent")
        except Exception:
            intent = None

        allowed = {"log_interaction", "edit_interaction", "get_interactions", "summarize", "follow_up", "other"}
        if intent not in allowed:
            retry_messages = [
                {
                    "role": "system",
                    "content": (
                        "Return JSON only: {\"intent\": \"log_interaction|edit_interaction|get_interactions|summarize|follow_up|other\"}."
                    ),
                },
                {"role": "user", "content": user_text},
            ]
            try:
                raw_retry = llm.complete_text(retry_messages, temperature=0, max_tokens=40)
                parsed_retry = extract_json(raw_retry) or {}
                intent = parsed_retry.get("intent")
            except Exception:
                intent = None

        if intent not in allowed:
            intent = "log_interaction"

        return {"intent": intent}

    def route(state: AgentState) -> str:
        return state.get("intent", "log_interaction")

    def build_response(state: AgentState) -> AgentState:
        if state.get("response"):
            return {}

        tool_result = state.get("tool_result")
        if tool_result:
            payload = json.dumps(tool_result, default=str)
            messages = [
                {"role": "system", "content": RESPONSE_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "User input: "
                        + state.get("user_input", "")
                        + "\nTool result: "
                        + payload
                    ),
                },
            ]
            response = llm.complete_text(messages, temperature=0.2, max_tokens=200)
            return {"response": response}

        messages = [
            {"role": "system", "content": GENERAL_CHAT_PROMPT},
            {"role": "user", "content": state.get("user_input", "")},
        ]
        response = llm.complete_text(messages, temperature=0.4, max_tokens=200)
        return {"response": response}

    graph = StateGraph(AgentState)
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("log_interaction", tools.log_interaction)
    graph.add_node("edit_interaction", tools.edit_interaction)
    graph.add_node("get_interactions", tools.get_interactions)
    graph.add_node("summarize_interaction", tools.summarize_interaction)
    graph.add_node("followup_suggestion", tools.followup_suggestion)
    graph.add_node("build_response", build_response)

    graph.set_entry_point("detect_intent")
    graph.add_conditional_edges(
        "detect_intent",
        route,
        {
            "log_interaction": "log_interaction",
            "edit_interaction": "edit_interaction",
            "get_interactions": "get_interactions",
            "summarize": "summarize_interaction",
            "follow_up": "followup_suggestion",
            "other": "build_response",
        },
    )

    graph.add_edge("log_interaction", "build_response")
    graph.add_edge("edit_interaction", "build_response")
    graph.add_edge("get_interactions", "build_response")
    graph.add_edge("summarize_interaction", "build_response")
    graph.add_edge("followup_suggestion", "build_response")
    graph.add_edge("build_response", END)

    return graph.compile()

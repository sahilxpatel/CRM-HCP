import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";

import { loadInteractions } from "../redux/interactionsSlice";

import { chatWithAgent } from "../services/api";

const ChatLogger = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Describe an HCP interaction and I will log it for you.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(loadInteractions());
  }, [dispatch]);

  const buildDecisionLine = (response) => {
    if (!response || !response.intent) {
      return "";
    }
    const intentMap = {
      log: "log_interaction",
      edit: "edit_interaction",
      get: "get_interactions",
      summarize: "summarize_interaction",
      followup: "followup_suggestion",
      other: "other",
    };
    const toolMap = {
      log: "LogInteractionTool",
      edit: "EditInteractionTool",
      get: "GetInteractionsTool",
      summarize: "SummarizeInteractionTool",
      followup: "FollowUpSuggestionTool",
    };
    const intentName = intentMap[response.intent] || response.intent;
    const toolName = toolMap[response?.tool_result?.action] || "GeneralResponse";
    return `Intent: ${intentName} -> Tool: ${toolName}`;
  };

  const buildStatus = (payload) => {
    if (!payload) {
      return "";
    }
    if (payload.error) {
      return `Error: ${payload.error}`;
    }
    if (payload.action === "log" && payload.interaction) {
      return `OK: Interaction logged for ${payload.interaction.hcp_name} on ${payload.interaction.date}`;
    }
    if (payload.action === "edit" && payload.interaction) {
      return `OK: Interaction updated for ${payload.interaction.hcp_name}`;
    }
    if (payload.action === "get" && Array.isArray(payload.items)) {
      return `OK: Loaded ${payload.items.length} interactions`;
    }
    if (payload.action === "summarize" && payload.summary) {
      return `OK: Summary generated`;
    }
    if (payload.action === "followup" && payload.suggestion) {
      return "OK: Follow-up suggestion ready";
    }
    return "";
  };

  const handleSend = async () => {
    if (!input.trim()) {
      return;
    }

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatWithAgent(userMessage.content);
      setStatus(buildStatus(response.tool_result));
      const decisionLine = buildDecisionLine(response);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response, meta: decisionLine },
      ]);
      // Give backend ~300ms to commit DB so we fetch the latest data
      setTimeout(() => {
        dispatch(loadInteractions());
      }, 300);
    } catch (error) {
      setStatus("Error: Could not reach the agent");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I could not reach the agent. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Conversational Logger</h2>
      <div className="chat-window">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`chat-bubble ${message.role}`}
          >
            <span className="chat-label">
              {message.role === "user" ? "User" : "AI"}
            </span>
            {message.content}
            {message.meta ? (
              <span className="chat-meta">{message.meta}</span>
            ) : null}
          </div>
        ))}
        {loading ? (
          <div className="chat-bubble assistant">
            <span className="chat-label">AI</span>
            Thinking...
          </div>
        ) : null}
      </div>
      {status ? <div className="chat-status">{status}</div> : null}
      <div className="chat-input">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Log a visit, summarize notes, or ask for follow-up"
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
};

export default ChatLogger;

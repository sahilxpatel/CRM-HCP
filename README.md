# AI-First CRM: HCP Interaction Logging Module

An intelligent CRM module built for Healthcare Professionals (HCPs) that replaces manual data entry with a conversational AI interface. Powered by a **LangGraph agent**, this system seamlessly converts natural language conversations into structured database records, generates summaries, and provides context-aware follow-up suggestions.

## 🔗 Live Demo
- **Frontend**: https://crm-hcp.vercel.app/
- **Backend**: https://crm-hcp.onrender.com

## 🚀 Deployment

- Frontend deployed on Vercel
- Backend deployed on Render
- Database hosted on Neon PostgreSQL
- LLM powered by Groq API

> [!NOTE]
> Backend may take a few seconds to respond initially due to free-tier cold starts.

---

## 🚀 Key Features

- **Conversational Data Entry**: Chat naturally to log interactions (e.g., *"I met Dr. Shah yesterday and discussed diabetes medication pricing"*).
- **Intelligent Intent Routing**: The agent understands if you want to log a new interaction, edit an existing one, retrieve history, summarize notes, or get follow-up advice.
- **Automated Summarization**: Automatically generates concise summaries from long interaction notes.
- **Context-Aware Follow-Ups**: AI suggests practical next steps based on the sentiment and details of past interactions.
- **Dual Interface**: Supports both traditional form-based logging and an AI-powered chat interface.

---

## 🏗 Architecture

The system is built on a modern AI-native stack:

- **Frontend**: React (Redux for state management, Tailwind for UI)
- **Backend**: FastAPI (Python)
- **AI Engine**: LangGraph (Agent orchestration) & Groq LLM (Fast inference)
- **Database**: PostgreSQL (Relational storage via SQLAlchemy)

### System Flow
```mermaid
graph TD
    UI[React Frontend] -->|API Request| API[FastAPI Backend]
    API --> Agent[LangGraph Agent]
    
    subgraph LangGraph Decision Engine
        Agent -->|1. Intent Detection| Router{Router}
        Router -->|log_interaction| Tool1[LogInteractionTool]
        Router -->|edit_interaction| Tool2[EditInteractionTool]
        Router -->|get_interactions| Tool3[GetInteractionsTool]
        Router -->|summarize| Tool4[SummarizeInteractionTool]
        Router -->|follow_up| Tool5[FollowUpSuggestionTool]
    end
    
    Tool1 & Tool2 & Tool3 & Tool4 & Tool5 --> LLM[Groq LLM Extraction/Reasoning]
    LLM --> DB[(PostgreSQL)]
    DB --> Response[AI Response Builder]
    Response --> UI
```

---

## 🧠 LangGraph Tools Overview

1. **`LogInteractionTool`**: Converts free-form text into structured data. Automatically handles relative dates (e.g., "yesterday") and extracts HCP names and discussion details.
2. **`EditInteractionTool`**: Modifies existing records naturally (e.g., *"Update Dr. Shah's interaction to include our competitor discussion"*).
3. **`GetInteractionsTool`**: Retrieves a chronological history of stored interactions.
4. **`SummarizeInteractionTool`**: Condenses lengthy meeting notes or past records into a 2-3 sentence summary focusing on outcomes and concerns.
5. **`FollowUpSuggestionTool`**: Analyzes the sentiment of past interactions to suggest tailored, actionable next steps.

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL database
- [Groq API Key](https://console.groq.com/)

### 1. Backend Setup

```bash
# Navigate to backend directory or root depending on structure
pip install -r requirements.txt

# Configure your environment variables (.env)
GROQ_API_KEY=your_groq_api_key
GROQ_PRIMARY_MODEL=gemma2-9b-it
GROQ_FALLBACK_MODEL=llama-3.3-70b-versatile
GROQ_MOCK=0
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/crm_hcp

# Run the FastAPI server
uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
npm install
npm run dev
```

---

## 💬 Demo Guide

Want to see the AI in action? Try pasting these prompts into the chat UI in order:

1. **Log an interaction:** 
   > *"I met Dr. Shah yesterday and discussed diabetes pricing"*
2. **Update the record:** 
   > *"Update Dr. Shah interaction to include competitor discussion"*
3. **Ask for advice:** 
   > *"What should I do next for Dr. Shah?"*
4. **Review history:** 
   > *"Show my recent interactions"*
5. **Summarize a meeting:** 
   > *"Summarize my last meeting with Dr. Shah"*

---

## 💡 Why LangGraph?

Traditional chatbots rely on rigid `if/else` rules or basic chains. This project uses **LangGraph** to build a dynamic, stateful agent that can:
- Route intelligently between completely different specialized tools.
- Fall back gracefully to safe defaults without getting stuck in conversational loops.
- Maintain a strictly typed state (`AgentState`) throughout the execution cycle, ensuring predictable outputs.

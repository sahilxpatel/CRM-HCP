# AI-First CRM - HCP Interaction Logging Module

## What Makes This AI-First?
Traditional CRMs require manual data entry. This system allows:
- Free-form conversation converted into structured CRM data
- Automatic summarization of interactions
- Intelligent follow-up suggestions

The system reduces manual effort and improves decision-making using AI.

## Architecture Overview
React (Form + Chat UI)
        ↓
FastAPI Backend
        ↓
LangGraph Agent (Decision Engine)
        ↓
Groq LLM (Reasoning + Extraction)
        ↓
PostgreSQL Database

## LangGraph Agent Flow
User Input
   ↓
LLM Intent Detection
   ↓
LangGraph Conditional Routing
   ↓
Selected Tool Execution
   ↓
Database / LLM Processing
   ↓
Response to User

- No hardcoded routing
- Fully LLM-driven decision making

## AI Tools (LangGraph)
1. LogInteractionTool
   - Converts natural language into structured data
   - Extracts: HCP name, date (supports relative dates like "yesterday"), interaction details
   - Generates AI summary
2. EditInteractionTool
   - Updates records using natural language
   - Example: "Update Dr. Shah interaction with pricing discussion"
3. GetInteractionsTool
   - Retrieves stored interaction history
4. SummarizeInteractionTool
   - Generates concise summaries from notes or past interactions
5. FollowUpSuggestionTool (Context-Aware)
   - Uses past interaction data to suggest next actions
   - Example: "Follow up in 2 weeks with clinical data"

## API Endpoints
- POST /log-interaction - Structured logging
- POST /chat - AI-powered interaction
- GET /interactions - Fetch all interactions
- PUT /interaction/{id} - Update interaction

## Example Chat Inputs (Demo Ready)
- I met Dr. Shah yesterday and discussed diabetes medication pricing
- Update Dr. Shah interaction to include competitor discussion
- Show my recent interactions
- Summarize my last meeting
- What should I do next for Dr. Shah?

## Demo Flow
1. Log interaction via chat:
   "I met Dr. Shah yesterday and discussed diabetes pricing"
2. AI extracts and stores structured data
3. Update interaction:
   "Update Dr. Shah interaction to include competitor discussion"
4. Ask for follow-up:
   "What should I do next for Dr. Shah?"
5. View interaction history with AI summaries

## Setup Instructions

### Backend
1. Install dependencies:
   pip install -r requirements.txt
2. Configure environment:
   GROQ_API_KEY=your_key
   GROQ_PRIMARY_MODEL=gemma2-9b-it
   GROQ_FALLBACK_MODEL=llama-3.3-70b-versatile
   GROQ_MOCK=0
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/crm_hcp
3. Run server:
   uvicorn app.main:app --reload

### Frontend
1. npm install
2. npm run dev

## Key Features
- Dual logging: Form + Conversational AI
- LLM-based intent detection
- Context-aware follow-up recommendations
- Automatic summarization
- Real-time interaction updates

## Why LangGraph?
LangGraph is used to:
- Enable dynamic decision-making using LLMs
- Route user input to appropriate tools without hardcoded logic
- Maintain a structured agent workflow

This ensures the system behaves like an intelligent assistant rather than a
rule-based application.

## Design Decisions
- LangGraph used for agent orchestration instead of simple routing
- Groq LLM chosen for fast inference
- PostgreSQL for structured interaction storage
- Redux for predictable frontend state management

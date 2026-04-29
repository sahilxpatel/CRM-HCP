from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.langgraph.agent import build_agent
from app.schemas.interaction import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    agent = build_agent(db)
    result = agent.invoke({"user_input": payload.message})
    response = result.get("response")
    if not response:
        raise HTTPException(status_code=500, detail="Agent did not return a response")
    return ChatResponse(
        response=response,
        intent=result.get("intent"),
        tool_result=result.get("tool_result"),
    )

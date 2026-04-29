from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class InteractionBase(BaseModel):
    hcp_name: str = Field(..., examples=["Dr. Alex Smith"])
    interaction_type: str = Field(..., examples=["Clinic visit"])
    date: date
    notes: str


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None
    summary: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    tool_result: Optional[Any] = None

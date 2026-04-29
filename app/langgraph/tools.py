import re
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.services.groq_client import GroqClient
from app.services.interaction_service import (
    create_interaction,
    get_interactions,
    summarize_notes,
    update_interaction,
)
from app.langgraph.prompts import (
    EDIT_PROMPT,
    EXTRACT_PROMPT,
    FOLLOWUP_PROMPT,
    SUMMARY_PROMPT,
    TARGET_PROMPT,
)
from app.langgraph.utils import clean_hcp_name, coerce_date, extract_json


class AgentTools:
    def __init__(self, llm: GroqClient, db: Session):
        self.llm = llm
        self.db = db

    def _serialize_interaction(self, interaction: Interaction) -> Dict[str, Any]:
        return {
            "id": interaction.id,
            "hcp_name": interaction.hcp_name,
            "interaction_type": interaction.interaction_type,
            "date": interaction.date.isoformat(),
            "notes": interaction.notes,
            "summary": interaction.summary,
            "created_at": interaction.created_at.isoformat()
            if interaction.created_at
            else None,
        }

    def _extract_target(self, user_text: str) -> Dict[str, Optional[Any]]:
        today = datetime.utcnow().date().isoformat()
        messages = [
            {"role": "system", "content": TARGET_PROMPT.format(today=today)},
            {"role": "user", "content": user_text},
        ]
        raw = self.llm.complete_text(messages, temperature=0, max_tokens=120)
        extracted = extract_json(raw) or {}
        return {
            "hcp_name": clean_hcp_name(extracted.get("hcp_name")),
            "date": coerce_date(extracted.get("date")),
        }

    def _find_interaction(
        self, hcp_name: Optional[str], on_date: Optional[date]
    ) -> Optional[Interaction]:
        query = self.db.query(Interaction)
        if hcp_name:
            query = query.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
        if on_date:
            query = query.filter(Interaction.date == on_date)
        return query.order_by(Interaction.date.desc(), Interaction.id.desc()).first()

    def _latest_interaction(self) -> Optional[Interaction]:
        return (
            self.db.query(Interaction)
            .order_by(Interaction.date.desc(), Interaction.id.desc())
            .first()
        )

    def _infer_sentiment(self, text: str) -> str:
        lowered = text.lower()
        low_interest_markers = [
            "not interested",
            "no interest",
            "uninterested",
            "declined",
            "not a fit",
            "too expensive",
            "pricing concern",
            "budget",
        ]
        if any(marker in lowered for marker in low_interest_markers):
            return "low_interest"
        return "neutral"

    def log_interaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = state.get("user_input", "")
        today = datetime.utcnow().date().isoformat()
        messages = [
            {"role": "system", "content": EXTRACT_PROMPT.format(today=today)},
            {"role": "user", "content": user_text},
        ]
        raw = self.llm.complete_text(messages, temperature=0.1, max_tokens=300)
        extracted = extract_json(raw) or {}
        cleaned_name = clean_hcp_name(extracted.get("hcp_name"))

        interaction_data = InteractionCreate(
            hcp_name=(cleaned_name or "Unknown HCP").strip(),
            interaction_type=(extracted.get("interaction_type") or "Unknown").strip(),
            date=coerce_date(extracted.get("date")) or datetime.utcnow().date(),
            notes=(extracted.get("notes") or user_text).strip(),
        )

        summary = summarize_notes(interaction_data.notes, self.llm)
        interaction = create_interaction(self.db, interaction_data, summary=summary)

        return {
            "tool_result": {
                "action": "log",
                "interaction": self._serialize_interaction(interaction),
            },
            "intent": "log",
        }

    def edit_interaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = state.get("user_input", "")
        today = datetime.utcnow().date().isoformat()
        messages = [
            {"role": "system", "content": EDIT_PROMPT.format(today=today)},
            {"role": "user", "content": user_text},
        ]
        raw = self.llm.complete_text(messages, temperature=0.1, max_tokens=300)
        extracted = extract_json(raw) or {}
        cleaned_name = clean_hcp_name(extracted.get("hcp_name"))

        interaction_id = extracted.get("id")
        if not interaction_id:
            match = re.search(r"\b(\d+)\b", user_text)
            interaction_id = int(match.group(1)) if match else None

        interaction = None
        if interaction_id:
            interaction = (
                self.db.query(Interaction)
                .filter(Interaction.id == int(interaction_id))
                .first()
            )
        else:
            target_name = cleaned_name
            target_date = coerce_date(extracted.get("date"))
            if target_name or target_date:
                interaction = self._find_interaction(target_name, target_date)
            elif "last" in user_text.lower() or "recent" in user_text.lower():
                interaction = self._latest_interaction()

        if not interaction:
            return {
                "tool_result": {
                    "action": "edit",
                    "error": "No matching interaction found to update",
                },
                "intent": "edit",
            }

        notes_value = extracted.get("notes")
        notes_mode = extracted.get("notes_mode")
        if notes_value:
            if notes_mode not in {"append", "replace"}:
                notes_mode = "append"
            if notes_mode == "append":
                notes_value = f"{interaction.notes}\nUpdate: {notes_value}".strip()

        updates = InteractionUpdate(
            hcp_name=cleaned_name,
            interaction_type=extracted.get("interaction_type"),
            date=coerce_date(extracted.get("date")),
            notes=notes_value,
            summary=extracted.get("summary"),
        )

        updated = update_interaction(self.db, interaction.id, updates)
        if not updated:
            return {
                "tool_result": {
                    "action": "edit",
                    "error": f"Interaction {interaction.id} not found",
                },
                "intent": "edit",
            }

        return {
            "tool_result": {
                "action": "edit",
                "interaction": self._serialize_interaction(updated),
            },
            "intent": "edit",
        }

    def get_interactions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        interactions = get_interactions(self.db)
        serialized = [self._serialize_interaction(item) for item in interactions]
        return {
            "tool_result": {"action": "get", "items": serialized},
            "intent": "get",
        }

    def summarize_interaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = state.get("user_input", "")
        lower_text = user_text.lower()
        match = re.search(r"\b(\d+)\b", user_text)
        if match:
            interaction_id = int(match.group(1))
            interaction = (
                self.db.query(Interaction)
                .filter(Interaction.id == interaction_id)
                .first()
            )
            if interaction:
                summary = summarize_notes(interaction.notes, self.llm)
                return {
                    "tool_result": {
                        "action": "summarize",
                        "interaction_id": interaction_id,
                        "summary": summary,
                    },
                    "intent": "summarize",
                }

        target = self._extract_target(user_text)
        has_target = bool(target.get("hcp_name") or target.get("date"))
        interaction = None
        if has_target:
            interaction = self._find_interaction(target.get("hcp_name"), target.get("date"))
        if not interaction and ("last" in lower_text or "recent" in lower_text):
            interaction = self._latest_interaction()
        if interaction:
            summary = summarize_notes(interaction.notes, self.llm)
            return {
                "tool_result": {
                    "action": "summarize",
                    "interaction_id": interaction.id,
                    "summary": summary,
                },
                "intent": "summarize",
            }
        if has_target or "last" in lower_text or "recent" in lower_text:
            return {
                "tool_result": {
                    "action": "summarize",
                    "error": "No matching interaction found to summarize",
                },
                "intent": "summarize",
            }

        messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": user_text},
        ]
        summary = self.llm.complete_text(messages, temperature=0.2, max_tokens=200)
        return {
            "tool_result": {"action": "summarize", "summary": summary},
            "intent": "summarize",
        }

    def followup_suggestion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_text = state.get("user_input", "")
        lower_text = user_text.lower()
        target = self._extract_target(user_text)
        interaction = None
        if target.get("hcp_name") or target.get("date"):
            interaction = self._find_interaction(target.get("hcp_name"), target.get("date"))
        if not interaction and ("last" in lower_text or "recent" in lower_text):
            interaction = self._latest_interaction()

        if interaction:
            context = (
                f"HCP: {interaction.hcp_name}\n"
                f"Date: {interaction.date.isoformat()}\n"
                f"Type: {interaction.interaction_type}\n"
                f"Notes: {interaction.notes}\n"
                f"Summary: {interaction.summary or ''}"
            )
            sentiment_source = f"{user_text}\n{interaction.notes}\n{interaction.summary or ''}"
        else:
            context = user_text
            sentiment_source = user_text

        sentiment = self._infer_sentiment(sentiment_source)

        messages = [
            {"role": "system", "content": FOLLOWUP_PROMPT},
            {
                "role": "user",
                "content": (
                    "User input: "
                    + user_text
                    + "\nSentiment: "
                    + sentiment
                    + "\n\nContext:\n"
                    + context
                ),
            },
        ]
        suggestion = self.llm.complete_text(messages, temperature=0.2, max_tokens=120)
        return {
            "tool_result": {
                "action": "followup",
                "suggestion": suggestion,
            },
            "intent": "followup",
        }

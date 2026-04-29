from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.langgraph.utils import clean_hcp_name
from app.services.groq_client import GroqClient


def summarize_notes(notes: str, llm: Optional[GroqClient] = None) -> str:
    client = llm or GroqClient()
    messages = [
        {
            "role": "system",
            "content": (
                "Summarize the interaction notes in 2-3 concise sentences. "
                "Focus on key outcomes and next steps."
            ),
        },
        {"role": "user", "content": notes},
    ]
    return client.complete_text(messages, temperature=0.2, max_tokens=200)


def create_interaction(
    db: Session,
    data: InteractionCreate,
    summary: Optional[str] = None,
) -> Interaction:
    existing = (
        db.query(Interaction)
        .filter(
            func.lower(Interaction.hcp_name) == data.hcp_name.lower(),
            Interaction.date == data.date,
        )
        .first()
    )
    if existing:
        incoming_notes = data.notes.strip()
        if incoming_notes and incoming_notes not in existing.notes:
            existing.notes = f"{existing.notes}\nUpdate: {incoming_notes}".strip()
        if summary:
            existing.summary = summary
        else:
            try:
                existing.summary = summarize_notes(existing.notes)
            except Exception:
                existing.summary = existing.notes[:200]
        db.commit()
        db.refresh(existing)
        return existing

    final_summary = summary
    if not final_summary:
        try:
            final_summary = summarize_notes(data.notes)
        except Exception:
            final_summary = data.notes[:200]

    interaction = Interaction(
        hcp_name=data.hcp_name,
        interaction_type=data.interaction_type,
        date=data.date,
        notes=data.notes,
        summary=final_summary,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interactions(db: Session) -> List[Interaction]:
    items = (
        db.query(Interaction)
        .order_by(Interaction.date.desc(), Interaction.id.desc())
        .all()
    )
    seen = {}
    results = []
    to_delete = []
    touched = False

    for item in items:
        cleaned_name = clean_hcp_name(item.hcp_name) or item.hcp_name
        if cleaned_name != item.hcp_name:
            item.hcp_name = cleaned_name
            touched = True
        key = (cleaned_name.lower(), item.date)
        if key in seen:
            target = seen[key]
            if item.notes and item.notes not in target.notes:
                target.notes = f"{target.notes}\nUpdate: {item.notes}".strip()
                touched = True
            if item.summary and item.summary not in (target.summary or ""):
                target.summary = item.summary
                touched = True
            to_delete.append(item)
        else:
            seen[key] = item
            results.append(item)

    if to_delete:
        for item in to_delete:
            db.delete(item)
        touched = True

    if touched:
        db.commit()

    return results


def update_interaction(
    db: Session,
    interaction_id: int,
    updates: InteractionUpdate,
) -> Optional[Interaction]:
    interaction = (
        db.query(Interaction)
        .filter(Interaction.id == interaction_id)
        .first()
    )
    if not interaction:
        return None

    if updates.hcp_name is not None:
        interaction.hcp_name = updates.hcp_name
    if updates.interaction_type is not None:
        interaction.interaction_type = updates.interaction_type
    if updates.date is not None:
        interaction.date = updates.date
    if updates.notes is not None:
        interaction.notes = updates.notes

    if updates.summary is not None:
        interaction.summary = updates.summary
    elif updates.notes is not None:
        try:
            interaction.summary = summarize_notes(updates.notes)
        except Exception:
            interaction.summary = updates.notes[:200]

    db.commit()
    db.refresh(interaction)
    return interaction

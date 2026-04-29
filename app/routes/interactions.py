from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.interaction import (
    InteractionCreate,
    InteractionOut,
    InteractionUpdate,
)
from app.services.interaction_service import (
    create_interaction,
    get_interactions,
    update_interaction,
)

router = APIRouter()


@router.post("/log-interaction", response_model=InteractionOut)
def log_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db),
):
    return create_interaction(db, payload)


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return get_interactions(db)


@router.put("/interaction/{interaction_id}", response_model=InteractionOut)
def edit_interaction(
    interaction_id: int,
    payload: InteractionUpdate,
    db: Session = Depends(get_db),
):
    interaction = update_interaction(db, interaction_id, payload)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

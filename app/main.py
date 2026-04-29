from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import Base, engine
from app.models import interaction  # Ensures model metadata is registered.
from app.routes.chat import router as chat_router
from app.routes.interactions import router as interactions_router

app = FastAPI(title="AI-First CRM - HCP Interaction Logging")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "ok"}


app.include_router(interactions_router)
app.include_router(chat_router)

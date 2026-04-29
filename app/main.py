from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.database.db import Base, engine
from app.models import interaction  # register models
from app.routes.chat import router as chat_router
from app.routes.interactions import router as interactions_router

#  Create FastAPI app (disable default docs to avoid Render issues)
app = FastAPI(
    title="AI-First CRM - HCP Interaction Logging",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json"
)

#  Enable CORS (for Vercel frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to your Vercel URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Create DB tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


#  Root test route
@app.get("/")
def root():
    return {"status": "API is running 🚀"}


#  Custom Swagger UI (fixes /docs issue on Render)
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs"
    )


#  Optional Redoc UI
@app.get("/redoc", include_in_schema=False)
def redoc_ui():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="API Docs"
    )


#  Include routers
app.include_router(interactions_router)
app.include_router(chat_router)
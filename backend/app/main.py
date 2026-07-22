from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine
from app.models import (  # noqa: F401
    Conversation,
    Document,
    Message,
    Property,
    PropertyProfile,
    PropertyRawSource,
    Report,
    SavedProperty,
    User,
)
from app.routers import analysis, auth, chat, documents, properties, reports

app = FastAPI(
    title="AI Real Estate Showing Assistant",
    version="1.0.0",
    description="Verified property profile + AI assistant starter.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AI Real Estate Showing Assistant",
        "mode": "local-demo",
    }


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(properties.router, prefix="/properties", tags=["properties"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

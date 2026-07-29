"""Voice interaction API endpoints (using browser-based speech for FREE)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.llm_assistant_service import (
    ask_property_question,
    get_property_assistant_briefing,
)

router = APIRouter()


class TranscribeResponse(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str


class QuestionRequest(BaseModel):
    property_id: int
    question: str
    conversation_history: list[dict[str, str]] | None = None


class QuestionResponse(BaseModel):
    answer: str
    audio_url: str | None = None


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio():
    """
    Speech-to-text is handled by the browser (Web Speech API).
    This endpoint is kept for API compatibility but returns an error.
    """
    raise HTTPException(
        status_code=501,
        detail="Use browser's Web Speech API instead (free). Backend transcription disabled."
    )


@router.post("/speak")
async def speak_text():
    """
    Text-to-speech is handled by the browser (Web Speech API).
    This endpoint is kept for API compatibility but returns an error.
    """
    raise HTTPException(
        status_code=501,
        detail="Use browser's Web Speech API instead (free). Backend TTS disabled."
    )


@router.get("/properties/{property_id}/briefing")
def get_property_briefing(property_id: int, db: Session = Depends(get_db)):
    """
    Get an AI-generated briefing for a property (text only).
    
    Uses Google Gemini (FREE).
    """
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="Google API key not configured")

    try:
        briefing = get_property_assistant_briefing(db, property_id)
        return {"briefing": briefing}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {e}")


@router.get("/properties/{property_id}/briefing/audio")
def get_property_briefing_audio():
    """
    Audio briefings now use browser's TTS (free).
    Get text briefing from /briefing endpoint and use browser to speak it.
    """
    raise HTTPException(
        status_code=501,
        detail="Use /briefing endpoint to get text, then use browser TTS to speak it (free)."
    )


@router.post("/properties/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Ask a question about a property and get an AI-generated answer.
    
    Uses Google Gemini (FREE).
    Optionally provide conversation history for context-aware responses.
    """
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="Google API key not configured")

    try:
        answer = ask_property_question(
            db,
            request.property_id,
            request.question,
            request.conversation_history,
        )

        return QuestionResponse(answer=answer, audio_url=None)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {e}")


@router.post("/properties/ask/voice")
async def ask_question_voice():
    """
    Voice Q&A now uses browser's speech APIs (free).
    Use /properties/ask for text Q&A, then browser TTS to speak the answer.
    """
    raise HTTPException(
        status_code=501,
        detail="Use browser's Web Speech API for voice input/output (free)."
    )

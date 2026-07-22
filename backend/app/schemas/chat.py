from pydantic import BaseModel


class ChatRequest(BaseModel):
    property_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int | None = None

from pydantic import BaseModel


class DocumentUploadRequest(BaseModel):
    filename: str
    content: str | None = None


class DocumentUploadResponse(BaseModel):
    filename: str
    parsed_text: str
    status: str

from fastapi import APIRouter

from app.schemas.document import DocumentUploadRequest, DocumentUploadResponse
from app.services.document_service import parse_document

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(payload: DocumentUploadRequest):
    return parse_document(payload.filename, payload.content)

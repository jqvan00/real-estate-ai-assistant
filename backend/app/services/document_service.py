from app.schemas.document import DocumentUploadResponse


def parse_document(filename: str, content: str | None = None) -> DocumentUploadResponse:
    parsed = (content or "").strip()
    return DocumentUploadResponse(
        filename=filename,
        parsed_text=parsed,
        status="parsed",
    )

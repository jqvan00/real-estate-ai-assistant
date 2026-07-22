from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    title: str
    content: dict

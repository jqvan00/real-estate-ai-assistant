from pydantic import BaseModel


class PropertyAnalyzeRequest(BaseModel):
    address: str
    listing_url: str | None = None


class PropertyAnalyzeResponse(BaseModel):
    property_id: int
    address: str
    verified_profile: dict
    analysis: dict
    source_breakdown: dict


class PropertyOut(BaseModel):
    id: int
    address: str
    listing_url: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    verified_summary: str | None = None
    profile: dict | None = None

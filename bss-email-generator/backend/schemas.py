from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EmailGenerateRequest(BaseModel):
    purpose: str = Field(..., description="e.g. Interview Scheduling, Offer Follow-up")
    recipient_name: Optional[str] = ""
    designation: Optional[str] = ""
    key_points: str = Field(..., description="Free-text bullet points to weave into the email")
    tone: str = "Professional"
    length: str = "Standard"


class EmailRefineRequest(BaseModel):
    email_id: int
    refinement_instruction: str


class EmailResponse(BaseModel):
    id: int
    subject: str
    body: str


class HistoryItem(BaseModel):
    id: int
    purpose: str
    recipient_name: Optional[str] = None
    subject: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)

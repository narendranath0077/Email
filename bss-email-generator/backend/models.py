from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.database import Base


class EmailLog(Base):
    """
    Every generated email (and every refinement of it) gets a row here.
    parent_id links a refinement back to the email it improved on, so we
    can reconstruct the full "edit history" of a draft if needed later.
    """

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)

    purpose = Column(String, nullable=False)
    recipient_name = Column(String)
    designation = Column(String)
    key_points = Column(Text)
    tone = Column(String)
    length = Column(String)

    subject = Column(Text)
    body = Column(Text)

    refinement_instruction = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("email_logs.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

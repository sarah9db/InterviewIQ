from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class EmailInfo(BaseModel):
    gmail_message_id: Optional[str] = Field(default=None)
    sender_name: Optional[str] = Field(default=None)
    sender_email: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    interview_datetime: Optional[str] = Field(default=None, description="ISO-8601 when possible")
    meeting_link: Optional[str] = Field(default=None)
    subject: Optional[str] = Field(default=None)
    snippet: Optional[str] = Field(default=None)


class SheetRow(BaseModel):
    id: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    interview_datetime: Optional[str] = None
    meeting_link: Optional[str] = None
    subject: Optional[str] = None
    snippet: Optional[str] = None
    prep_doc: Optional[str] = None
    created_at: str
    updated_at: str

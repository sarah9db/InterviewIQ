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


class FilterResult(BaseModel):
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    score: int = 0
    company_role_points: int = 0
    strong_phrase_points: int = 0
    context_term_points: int = 0
    meeting_signal_points: int = 0
    negative_signal_points: int = 0
    blocked_sender_points: int = 0
    strong_confirmation: bool = False
    accepted: bool = False
    rejection_reason: Optional[str] = None
    matched_strong_phrases: list[str] = Field(default_factory=list)
    matched_context_terms: list[str] = Field(default_factory=list)
    matched_negative_signals: list[str] = Field(default_factory=list)
    timestamp: str = ""


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

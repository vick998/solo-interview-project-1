"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str
    session_id: str


class AskResponse(BaseModel):
    """Response for POST /ask."""

    answer: str


class UploadResponse(BaseModel):
    """Response for POST /upload."""

    message: str
    documents_added: int

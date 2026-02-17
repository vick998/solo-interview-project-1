"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel


class CreateChatRequest(BaseModel):
    """Request body for POST /chats."""

    title: str | None = None


class AddUrlsRequest(BaseModel):
    """Request body for POST /chats/{id}/add-urls."""

    urls: list[str]


class AskRequest(BaseModel):
    """Request body for POST /chats/{id}/ask."""

    question: str
    document_ids: list[str] | None = None
    model_id: str | None = None


class AskResponse(BaseModel):
    """Response for POST /chats/{id}/ask."""

    answer: str
    model_used: str


class UploadResponse(BaseModel):
    """Response for POST /chats/{id}/upload."""

    document_ids: list[str]
    failed: list[dict[str, str]] | None = None


class AddUrlsResponse(BaseModel):
    """Response for POST /chats/{id}/add-urls."""

    document_ids: list[str]
    failed: list[dict[str, str]] | None = None


class DocumentEnabledRequest(BaseModel):
    """Request body for PATCH /chats/{id}/documents/{doc_id}."""

    enabled: bool


class UpdateChatRequest(BaseModel):
    """Request body for PATCH /chats/{id}."""

    title: str | None = None

"""Document upload and management endpoints."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_repo
from app.api.schemas import (
    AddUrlsRequest,
    AddUrlsResponse,
    DocumentEnabledRequest,
    UploadResponse,
)
from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import IMAGE_EXTENSIONS, PDF_EXTENSIONS, extract_text
from app.extraction.url import download_from_url
from app.storage.chat_repository import ChatRepository
from app.storage.exceptions import ChatNotFoundError

router = APIRouter()
ALLOWED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


def _validate_file_extension(filename: str) -> None:
    """Raise HTTPException if file extension is not supported."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: '{suffix}'. Supported: {ALLOWED_EXTENSIONS}",
        )


@router.post("/{chat_id}/upload", response_model=UploadResponse)
async def upload(
    chat_id: str,
    files: list[UploadFile] = File(...),
    repo: ChatRepository = Depends(get_repo),
) -> UploadResponse:
    """Upload files to a chat. Partial success: returns document_ids and failed list."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    document_ids: list[str] = []
    failed: list[dict[str, str]] = []

    for upload_file in files:
        if not upload_file.filename:
            failed.append({"filename_or_url": "(no filename)", "error": "File has no filename"})
            continue
        try:
            _validate_file_extension(upload_file.filename)
        except HTTPException as e:
            failed.append({"filename_or_url": upload_file.filename, "error": str(e.detail)})
            continue

        content = await upload_file.read()
        if not content:
            continue

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(upload_file.filename).suffix,
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            text = extract_text(tmp_path)
            if text and text.strip():
                docs = await repo.add_documents(
                    chat_id,
                    [
                        {
                            "source_type": "file",
                            "source_path_or_url": upload_file.filename,
                            "display_name": upload_file.filename,
                            "extracted_text": text.strip(),
                            "enabled": True,
                        }
                    ],
                )
                document_ids.extend(docs)
        except (ExtractionError, UnsupportedFileTypeError) as e:
            failed.append({"filename_or_url": upload_file.filename, "error": str(e)})
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return UploadResponse(
        document_ids=document_ids,
        failed=failed if failed else None,
    )


@router.post("/{chat_id}/add-urls", response_model=AddUrlsResponse)
async def add_urls(
    chat_id: str,
    request: AddUrlsRequest,
    repo: ChatRepository = Depends(get_repo),
) -> AddUrlsResponse:
    """Add documents from URLs. Partial success: returns document_ids and failed list."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    document_ids: list[str] = []
    failed: list[dict[str, str]] = []

    for url in request.urls:
        try:
            tmp_path, display_name = download_from_url(url)
            try:
                text = extract_text(tmp_path)
                if text and text.strip():
                    docs = await repo.add_documents(
                        chat_id,
                        [
                            {
                                "source_type": "url",
                                "source_path_or_url": url,
                                "display_name": display_name,
                                "extracted_text": text.strip(),
                                "enabled": True,
                            }
                        ],
                    )
                    document_ids.extend(docs)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except (ExtractionError, UnsupportedFileTypeError, Exception) as e:
            failed.append({"filename_or_url": url, "error": str(e)})

    return AddUrlsResponse(
        document_ids=document_ids,
        failed=failed if failed else None,
    )


@router.patch("/{chat_id}/documents/{document_id}")
async def update_document_enabled(
    chat_id: str,
    document_id: str,
    request: DocumentEnabledRequest,
    repo: ChatRepository = Depends(get_repo),
) -> dict:
    """Toggle document enabled state."""
    await repo.ensure_init()
    try:
        await repo.set_document_enabled(chat_id, document_id, request.enabled)
    except ChatNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"id": document_id, "enabled": request.enabled}

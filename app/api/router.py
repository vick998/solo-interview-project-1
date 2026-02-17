"""API router with upload and ask endpoints."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from app.api.schemas import AskRequest, AskResponse, UploadResponse
from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import (
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    extract_text,
)
from app.qa.pipeline import answer
from app.storage.exceptions import SessionNotFoundError
from app.storage.session_store import SessionStore

router = APIRouter()
_store = SessionStore()


def get_store() -> SessionStore:
    """Dependency that returns the session store. Overridable in tests."""
    return _store


ALLOWED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


def _validate_file_extension(filename: str) -> None:
    """Raise HTTPException if file extension is not supported."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: '{suffix}'. Supported: {ALLOWED_EXTENSIONS}",
        )


@router.post("/upload", response_model=UploadResponse)
async def upload(
    files: list[UploadFile] = File(...),
    x_session_id: str | None = Header(None, alias="X-Session-ID"),
    store: SessionStore = Depends(get_store),
) -> UploadResponse:
    """Accept multipart files, extract text, and store by session."""
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Session-ID header",
        )
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided",
        )

    extracted_texts: list[str] = []

    for upload_file in files:
        if not upload_file.filename:
            raise HTTPException(
                status_code=400,
                detail="File has no filename",
            )
        _validate_file_extension(upload_file.filename)

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
                extracted_texts.append(text.strip())
        except (ExtractionError, UnsupportedFileTypeError) as e:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to extract: {e}",
            ) from e
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    store.add_documents(x_session_id, extracted_texts)

    return UploadResponse(
        message="Documents uploaded successfully",
        documents_added=len(extracted_texts),
    )


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    store: SessionStore = Depends(get_store),
) -> AskResponse:
    """Answer a question using documents from the given session."""
    try:
        docs = store.get_documents(request.session_id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e

    result = answer(request.question, docs)
    return AskResponse(answer=result)

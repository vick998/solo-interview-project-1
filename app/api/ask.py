"""Ask/QA endpoint."""

import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_repo
from app.api.schemas import AskRequest, AskResponse
from app.config import QA_DEFAULT_MODEL, QA_MODELS
from app.qa.pipeline import answer_with_history
from app.storage.chat_repository import ChatRepository
from app.storage.exceptions import ChatNotFoundError

router = APIRouter()


def _derive_title(question: str) -> str:
    """Derive chat title from first question: 5 words, max 50 chars."""
    words = question.strip().split()[:5]
    title = " ".join(words)
    return title[:50] if len(title) > 50 else title


def _validate_model_id(model_id: str) -> None:
    """Raise HTTPException if model_id is invalid."""
    valid_ids = {m["id"] for m in QA_MODELS}
    if model_id not in valid_ids:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid model_id: '{model_id}'. Valid: {valid_ids}",
        )


@router.post("/{chat_id}/ask", response_model=AskResponse)
async def ask(
    chat_id: str,
    request: AskRequest,
    repo: ChatRepository = Depends(get_repo),
) -> AskResponse:
    """Answer a question using documents from the chat."""
    await repo.ensure_init()
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")

    model_id = request.model_id or QA_DEFAULT_MODEL
    _validate_model_id(model_id)

    docs = await repo.get_documents(
        chat_id,
        enabled_only=request.document_ids is None,
        document_ids=request.document_ids,
    )
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="At least one document is required. Upload documents first.",
        )

    messages = await repo.get_messages(chat_id, limit=5)
    history = [(m["question"], m["answer"]) for m in messages]

    doc_texts = [d["extracted_text"] for d in docs if d.get("extracted_text")]
    t0 = time.perf_counter()
    answer_text = answer_with_history(
        request.question,
        doc_texts,
        history,
        model_id=model_id,
    )
    inference_time = time.perf_counter() - t0

    await repo.add_message(
        chat_id, request.question, answer_text, model_id, inference_time=inference_time
    )

    if not messages and chat.get("title") is None:
        title = _derive_title(request.question)
        try:
            await repo.update_chat_title(chat_id, title)
        except ChatNotFoundError:
            pass

    return AskResponse(
        answer=answer_text, model_used=model_id, inference_time=inference_time
    )

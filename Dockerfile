# Stage 1 — Builder
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies only (cached across builds via mount; deps change less often than app)
COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy app and sync project (fast when only app changes)
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage 2 — Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment and app from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app

ENV PATH="/app/.venv/bin:$PATH"

# Pre-download models at build time (HuggingFace + EasyOCR)
RUN python -c "\
from app.qa.pipeline import _get_pipeline;\
from app.extraction.ocr import _get_reader;\
_get_pipeline();\
_get_reader()\
"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

"""Shared Hugging Face Inference API client."""

import os

from huggingface_hub import InferenceClient

INFERENCE_TIMEOUT = 120  # seconds


def get_hf_client() -> InferenceClient:
    """Return InferenceClient for HF Inference API."""
    token = os.environ.get("HF_TOKEN")
    if not token or not token.strip():
        raise ValueError(
            "HF_TOKEN environment variable is required. "
            "Set it in .env or pass -e HF_TOKEN=... when running."
        )
    return InferenceClient(
        provider="hf-inference",
        api_key=token,
        timeout=INFERENCE_TIMEOUT,
    )

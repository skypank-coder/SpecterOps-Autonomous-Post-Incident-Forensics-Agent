"""
Gemini API client — google-genai SDK.

IMPORTANT for current Gemini models (claude-opus-4-8 era guidance): do NOT pass
temperature, top_p, or top_k to GenerateContentConfig — they cause 400 errors.
Use max_output_tokens ONLY.

The blocking SDK call is dispatched to a worker thread so it never stalls the
asyncio event loop (keeping the SSE heartbeat responsive). If no API key is
configured the client raises, and each agent falls back to its built-in
scenario-accurate response so the demo still runs end-to-end.
"""
from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Ordered candidate models. The first one that successfully answers is cached
# for the rest of the process. This keeps the live demo working even if a
# specific preview model has been retired by the time it runs — a real risk for
# a pinned "preview" id. Override the whole list with GEMINI_MODEL if desired.
# Stable-first. Flash leads: fast (good for a live demo), generous free tier, and
# reliably available. Pro is tried next for higher-quality reasoning. The chain
# means a single retired/unavailable id never breaks the demo.
_DEFAULT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]
_env_model = os.getenv("GEMINI_MODEL", "").strip()
MODEL_CANDIDATES = ([_env_model] + _DEFAULT_MODELS) if _env_model else _DEFAULT_MODELS
MODEL = MODEL_CANDIDATES[0]  # primary / advertised model

_PLACEHOLDERS = {"", "your_gemini_api_key_here", "your_key", "changeme", "your_gcp_project_id"}
_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Prefer Vertex AI (Google Cloud) when configured. On Cloud Run, auth is the
# service's own identity (Application Default Credentials) — no key needed. Set
# GOOGLE_GENAI_USE_VERTEXAI=true and GOOGLE_CLOUD_PROJECT to enable it.
_USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")
_GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
_GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1").strip() or "us-central1"

_client = None
_provider = "none"
if _USE_VERTEX and _GCP_PROJECT and _GCP_PROJECT not in _PLACEHOLDERS:
    try:
        _client = genai.Client(vertexai=True, project=_GCP_PROJECT, location=_GCP_LOCATION)
        _provider = "vertex"
    except Exception:  # pragma: no cover - defensive
        _client = None
if _client is None and _API_KEY and _API_KEY not in _PLACEHOLDERS:
    try:
        _client = genai.Client(api_key=_API_KEY)
        _provider = "aistudio"
    except Exception:  # pragma: no cover - defensive
        _client = None


def provider() -> str:
    """'vertex' (Google Cloud), 'aistudio', or 'none'."""
    return _provider


# The model confirmed to work in this process (filled lazily on first call).
_active_model: str | None = None


def gemini_available() -> bool:
    return _client is not None


def active_model() -> str:
    return _active_model or MODEL


def _generate_sync(prompt: str, system: str, max_tokens: int) -> str:
    global _active_model
    config = types.GenerateContentConfig(max_output_tokens=max_tokens)
    if system:
        config.system_instruction = system

    # Try the previously confirmed model first, then the rest of the list.
    ordered: list[str] = []
    for name in ([_active_model] if _active_model else []) + list(MODEL_CANDIDATES):
        if name and name not in ordered:
            ordered.append(name)

    last_error: Exception | None = None
    for model_name in ordered:
        try:
            response = _client.models.generate_content(
                model=model_name, contents=prompt, config=config
            )
            _active_model = model_name
            return response.text or ""
        except Exception as exc:  # try the next candidate
            last_error = exc
            if _active_model == model_name:
                _active_model = None  # cached model failed; stop trusting it
            continue

    raise RuntimeError(f"All Gemini model candidates failed: {last_error}")


async def gemini_reason(prompt: str, system: str = "", max_tokens: int = 4096) -> str:
    """Standard Gemini call returning text. Raises if Gemini is unavailable."""
    if _client is None:
        raise RuntimeError("GEMINI_API_KEY not configured — using offline fallback")
    return await asyncio.to_thread(_generate_sync, prompt, system, max_tokens)


async def gemini_json(prompt: str, system: str = "", max_tokens: int = 8192) -> str:
    """
    Gemini call expecting JSON output.

    Appends a strict JSON-only instruction to the system prompt. The caller MUST
    use the JSON safety pattern when parsing the return value.
    """
    json_instruction = (
        "CRITICAL REQUIREMENT: Your entire response must be valid JSON only. "
        "Start with { and end with }. "
        "No markdown code fences. No explanation text before or after the JSON. "
        "No trailing commas. All strings must use double quotes."
    )
    combined_system = f"{system}\n\n{json_instruction}" if system else json_instruction
    return await gemini_reason(prompt, combined_system, max_tokens)

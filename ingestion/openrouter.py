"""
OpenRouter ingestion source.
Uses the public /api/v1/models endpoint — no API key required.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from models.llm import ModelEntry, PricingInfo

logger = logging.getLogger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
REQUEST_TIMEOUT = 30.0

PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "meta-llama": "Meta",
    "mistralai": "Mistral AI",
    "cohere": "Cohere",
    "qwen": "Qwen / Alibaba",
    "deepseek": "DeepSeek",
    "microsoft": "Microsoft",
    "amazon": "Amazon",
    "01-ai": "01.AI",
    "perplexity": "Perplexity",
    "nousresearch": "Nous Research",
    "x-ai": "xAI",
    "openrouter": "OpenRouter",
    "huggingfaceh4": "HuggingFace",
    "nvidia": "NVIDIA",
}

# Model IDs / name fragments to skip (gated, broken, or irrelevant for savings radar)
_SKIP_SUFFIXES = (":nitro", ":extended", ":beta")


def _provider_from_id(model_id: str) -> tuple[str, str]:
    """Extract (provider_id, provider_name) from a model ID like 'openai/gpt-4o'."""
    if "/" in model_id:
        raw = model_id.split("/")[0].lower()
        return raw, PROVIDER_DISPLAY_NAMES.get(raw, raw.replace("-", " ").title())
    return "unknown", "Unknown"


def _parse_price(value: Any) -> float:
    """Convert per-token price string → price per 1M tokens in USD."""
    try:
        if value is None:
            return 0.0
        per_token = float(value)
        return per_token * 1_000_000
    except (ValueError, TypeError):
        return 0.0


def _infer_tags(model_id: str, name: str, description: str) -> list[str]:
    """Heuristic capability tags derived from model metadata."""
    tags: list[str] = []
    text = f"{model_id} {name} {description}".lower()

    if any(k in text for k in ["code", "coder", "codestral", "coding", "starcoder"]):
        tags.append("code")
    if any(k in text for k in ["vision", "-vl", "visual", "image", "multimodal", "pixtral"]):
        tags.append("vision")
    if any(k in text for k in ["instruct", "chat", "assistant", "it"]):
        tags.append("chat")
    if any(k in text for k in ["128k", "200k", "1m context", "long-context", "long context"]):
        tags.append("long-context")
    if ":free" in model_id:
        tags.append("free-variant")
    if any(k in text for k in ["fast", "flash", "turbo", "mini", "haiku", "nano"]):
        tags.append("fast")
    if any(k in text for k in ["reason", "r1", "o1", "o3", "thinking"]):
        tags.append("reasoning")

    # All models are assumed to handle chat unless tagged otherwise
    if "chat" not in tags:
        tags.append("chat")

    return tags


async def fetch_openrouter_models() -> list[ModelEntry]:
    """Fetch all available models from the OpenRouter public API."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.get(
                OPENROUTER_MODELS_URL,
                headers={"User-Agent": "TokenHunter/0.1 (+https://github.com/token-hunter)"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching OpenRouter models: %s", exc)
            return []
        except Exception as exc:
            logger.error("Unexpected error fetching OpenRouter models: %s", exc)
            return []

    models: list[ModelEntry] = []
    now = datetime.utcnow()

    for item in data.get("data", []):
        model_id: str = item.get("id", "")
        if not model_id:
            continue

        # Skip premium/extended variants — they are cost-optimised differently
        if any(model_id.endswith(s) for s in _SKIP_SUFFIXES):
            continue

        name: str = item.get("name") or model_id
        description: str = item.get("description") or ""
        context_length: int = int(item.get("context_length") or 0)

        pricing_raw: dict = item.get("pricing") or {}
        input_price = _parse_price(pricing_raw.get("prompt"))
        output_price = _parse_price(pricing_raw.get("completion"))
        is_free = (input_price == 0.0 and output_price == 0.0)

        provider_id, provider_name = _provider_from_id(model_id)
        tags = _infer_tags(model_id, name, description)

        models.append(
            ModelEntry(
                id=model_id,
                name=name,
                provider_id=provider_id,
                provider_name=provider_name,
                pricing=PricingInfo(
                    input_per_1m=input_price,
                    output_per_1m=output_price,
                    is_free=is_free,
                ),
                context_length=context_length,
                description=description,
                tags=tags,
                source="openrouter",
                fetched_at=now,
            )
        )

    logger.info("OpenRouter: fetched %d models (%d free)",
                len(models), sum(1 for m in models if m.is_free))
    return models

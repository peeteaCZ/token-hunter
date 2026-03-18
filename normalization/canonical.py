"""
Simple canonical matching rules for provider/model IDs.
"""

from __future__ import annotations

import re


def canonicalize_provider_id(value: str) -> str:
    text = _slugify(value)
    provider_aliases = {
        "google-ai": "google",
        "googleai": "google",
        "google-genai": "google",
        "open-ai": "openai",
    }
    return provider_aliases.get(text, text)


def canonicalize_model_name(value: str) -> str:
    text = _slugify(value)

    replacements = {
        "gpt4o-mini": "gpt-4o-mini",
        "gpt-4o-mini-latest": "gpt-4o-mini",
        "gpt-4o-mini-preview": "gpt-4o-mini",
        "gpt41-mini": "gpt-4.1-mini",
        "gpt-4-1-mini": "gpt-4.1-mini",
        "gpt-4.1-mini-latest": "gpt-4.1-mini",
        "gpt41": "gpt-4.1",
        "gpt-4-1": "gpt-4.1",
        "gpt-4o-latest": "gpt-4o",
        "o3mini": "o3-mini",
        "o4mini": "o4-mini",
        "claude-3-haiku-20240307": "claude-3-haiku",
        "claude-3-haiku-latest": "claude-3-haiku",
        "claude3-haiku": "claude-3-haiku",
        "claude-3-5-haiku-latest": "claude-3.5-haiku",
        "claude35-haiku": "claude-3.5-haiku",
        "claude-3-7-sonnet-latest": "claude-3.7-sonnet",
        "claude37-sonnet": "claude-3.7-sonnet",
        "claude-sonnet-4-20250514": "claude-sonnet-4",
        "claude-opus-4-20250514": "claude-opus-4",
        "gemini-1-5-flash": "gemini-1.5-flash",
        "gemini-1-5-flash-latest": "gemini-1.5-flash",
        "gemini15flash": "gemini-1.5-flash",
        "gemini-1-5-pro": "gemini-1.5-pro",
        "gemini-1-5-pro-latest": "gemini-1.5-pro",
        "gemini15pro": "gemini-1.5-pro",
        "gemini-2-0-flash": "gemini-2.0-flash",
        "gemini20flash": "gemini-2.0-flash",
        "gemini-2-5-flash": "gemini-2.5-flash",
        "gemini25flash": "gemini-2.5-flash",
        "gemini-2-5-pro": "gemini-2.5-pro",
        "gemini25pro": "gemini-2.5-pro",
    }
    if text in replacements:
        return replacements[text]

    text = re.sub(r"-latest$", "", text)
    text = re.sub(r"-preview$", "", text)
    text = re.sub(r"-\d{8}$", "", text)
    text = re.sub(r"-v\d+$", "", text)

    if text.startswith("gpt-4-1"):
        text = text.replace("gpt-4-1", "gpt-4.1", 1)
    if text.startswith("claude-3-5"):
        text = text.replace("claude-3-5", "claude-3.5", 1)
    if text.startswith("claude-3-7"):
        text = text.replace("claude-3-7", "claude-3.7", 1)
    if text.startswith("gemini-1-5"):
        text = text.replace("gemini-1-5", "gemini-1.5", 1)
    if text.startswith("gemini-2-0"):
        text = text.replace("gemini-2-0", "gemini-2.0", 1)
    if text.startswith("gemini-2-5"):
        text = text.replace("gemini-2-5", "gemini-2.5", 1)

    return text


def canonicalize_route(provider_id: str, model_name_or_route: str) -> str:
    provider = canonicalize_provider_id(provider_id)
    if "/" in model_name_or_route:
        raw_provider, raw_model = model_name_or_route.split("/", 1)
        provider = canonicalize_provider_id(raw_provider)
        model = canonicalize_model_name(raw_model)
    else:
        model = canonicalize_model_name(model_name_or_route)
    return f"{provider}/{model}"


def _slugify(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("_", "-").replace("/", "-").replace(" ", "-")
    text = text.replace("(", "-").replace(")", "-")
    text = text.replace(".", ".")
    text = re.sub(r"[^a-z0-9.\-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")

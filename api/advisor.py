"""
AI advisor powered by Groq.
Answers natural-language questions about the current model radar.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from groq import AsyncGroq

from config.settings import settings

if TYPE_CHECKING:
    from models.llm import ModelEntry

logger = logging.getLogger(__name__)

_GROQ_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 600

_SYSTEM_PROMPT = """\
Jsi Token Hunter — savings-first poradce pro LLM modely a AI API.
Tvůj úkol je pomáhat uživatelům ušetřit za AI. Odpovídáš krátce, konkrétně a česky.
Základ pro doporučení jsou POUZE data z aktuálního radaru (viz níže).
Nikdy nevymýšlej ceny ani modely, které v datech nejsou.
Pokud data nestačí, řekni to upřímně.
Formát odpovědi: krátký odstavec + 2–4 odrážky s konkrétními modely.
"""


def _build_context(models: list[ModelEntry]) -> str:
    """Compress current model data into a compact LLM-friendly summary."""
    free = [m for m in models if m.is_free]
    paid = sorted(
        [m for m in models if not m.is_free and m.combined_price > 0],
        key=lambda m: m.combined_price,
    )

    lines = [f"Celkem modelů: {len(models)}. Zdarma: {len(free)}.\n"]

    lines.append("=== TOP 8 ZDARMA ===")
    for m in free[:8]:
        ctx = f"{m.context_length // 1000}K ctx" if m.context_length else ""
        lines.append(f"- {m.name} ({m.provider_name}) {ctx} | tagy: {', '.join(m.tags[:3])}")

    lines.append("\n=== TOP 10 NEJLEVNĚJŠÍ PLACENÉ (in/out za 1M tokenů) ===")
    for m in paid[:10]:
        lines.append(
            f"- {m.name} ({m.provider_name}) "
            f"${m.pricing.input_per_1m:.4f} in / ${m.pricing.output_per_1m:.4f} out"
            + (f" | ctx {m.context_length // 1000}K" if m.context_length else "")
        )

    # Highlight notable code models
    code_models = [m for m in models if "code" in m.tags][:5]
    if code_models:
        lines.append("\n=== CODING MODELY ===")
        for m in code_models:
            price = "FREE" if m.is_free else f"${m.pricing.input_per_1m:.4f}/${m.pricing.output_per_1m:.4f}"
            lines.append(f"- {m.name} ({m.provider_name}) {price}")

    return "\n".join(lines)


async def ask_advisor(question: str, models: list[ModelEntry]) -> str:
    """Send a question to Groq and return the answer string."""
    if not settings.GROQ_API_KEY:
        return "⚠ GROQ_API_KEY není nastaven. Přidej ho do .env.local."

    if not models:
        return "⚠ Data o modelech nejsou zatím dostupná. Zkus to za chvilku."

    context = _build_context(models)
    full_system = f"{_SYSTEM_PROMPT}\n\n=== AKTUÁLNÍ RADAR ===\n{context}"

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    try:
        response = await client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": question},
            ],
            max_tokens=_MAX_TOKENS,
            temperature=0.3,
        )
        return response.choices[0].message.content or "Bez odpovědi."
    except Exception as exc:
        logger.error("Groq advisor error: %s", exc)
        return f"⚠ Chyba při komunikaci s AI: {exc}"

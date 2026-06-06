"""OpenAI veya Google Gemini ile forum bilgisi destekli cevap uretimi."""

from __future__ import annotations

import logging

from firstmyko_bot.config import (
    AI_ENABLED,
    AI_ENGINE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LINKS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from firstmyko_bot.i18n import GREETING, detect_language
from firstmyko_bot.knowledge import format_topic_context, search_topics

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "tr": "Turkce",
    "en": "English",
    "es": "Spanish (Latin America / Peru)",
    "ar": "Arabic",
}


def ai_provider_label() -> str:
    if AI_ENGINE == "gemini":
        return f"Aktif (Gemini {GEMINI_MODEL})"
    if AI_ENGINE == "openai":
        return f"Aktif (OpenAI {OPENAI_MODEL})"
    return "Kapali — GEMINI_API_KEY veya OPENAI_API_KEY ekleyin"


def _system_prompt(lang: str) -> str:
    lang_name = LANG_NAMES.get(lang, "Turkce")
    greeting = GREETING.get(lang, GREETING["tr"])
    return f"""Sen FIRSTMYKO V1098 Old-USKO Knight Online sunucusunun resmi Discord asistanisin.

ONEMLI: Cevabini {lang_name} dilinde yaz. Kullanici hangi dilde sorduysa o dilde yanit ver.

Hitap tarzi (cevabin basinda kullan):
{greeting}

Gorevlerin:
1. Oyunculara samimi, sicak ve profesyonel hitap et.
2. Cevaplari SADECE verilen forum bilgi tabanindaki iceriklere dayandir.
3. Bilgi yoksa tahmin etme; forum linkine yonlendir.
4. Mutlaka en alakali forum konusunun TAM URL linkini ver (firstmyko.net/threads/...).
5. Kisa ozet + dogrudan konu linki ver. Max ~900 karakter.

Resmi linkler:
- Forum: {LINKS['forum']}
- Web: {LINKS['website']}
- Yenilikler: {LINKS['yenilikler']}
- PUS: {LINKS['pus']}
- Rehber: {LINKS['rehber']}
"""


def _fallback_answer(lang: str, topics: list[dict]) -> tuple[str, list[dict]]:
    if topics:
        lines = [GREETING.get(lang, GREETING["tr"]), ""]
        for t in topics[:2]:
            lines.append(f"📌 **{t['title']}**")
            lines.append(f"🔗 {t['url']}\n")
        return "\n".join(lines), topics
    return (
        f"{GREETING.get(lang, GREETING['tr'])}\n\nForum: {LINKS['forum']}",
        [],
    )


def _call_gemini(system: str, user: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system,
    )
    response = model.generate_content(
        user,
        generation_config={
            "max_output_tokens": 900,
            "temperature": 0.4,
        },
    )
    return (response.text or "").strip()


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=900,
        temperature=0.4,
    )
    return (response.choices[0].message.content or "").strip()


def generate_answer(
    question: str,
    lang: str | None = None,
    topics: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    if lang is None:
        lang = detect_language(question)
    if topics is None:
        topics = search_topics(question, limit=5)

    context = format_topic_context(topics)

    if not AI_ENABLED:
        return _fallback_answer(lang, topics)

    system = _system_prompt(lang)
    user_prompt = (
        f"Kullanici sorusu: {question}\n\n"
        f"Forum bilgi tabani:\n{context}\n\n"
        f"Yukaridaki konulara dayanarak {LANG_NAMES.get(lang, 'Turkce')} dilinde cevap ver. "
        "En alakali konunun tam URL'sini mutlaka ekle."
    )

    try:
        if AI_ENGINE == "gemini":
            answer = _call_gemini(system, user_prompt)
        else:
            answer = _call_openai(system, user_prompt)
        return answer, topics
    except Exception as exc:
        logger.exception("AI hatasi (%s): %s", AI_ENGINE, exc)
        return _fallback_answer(lang, topics)

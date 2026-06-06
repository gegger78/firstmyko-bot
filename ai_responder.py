"""OpenAI ile forum bilgisi destekli cevap uretimi."""

from __future__ import annotations

import logging

from openai import OpenAI

from firstmyko_bot.config import AI_ENABLED, LINKS, OPENAI_API_KEY, OPENAI_MODEL
from firstmyko_bot.i18n import GREETING, detect_language
from firstmyko_bot.knowledge import format_topic_context, search_topics

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "tr": "Turkce",
    "en": "English",
    "es": "Spanish (Latin America / Peru)",
    "ar": "Arabic",
}


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
        if topics:
            lines = [GREETING.get(lang, GREETING["tr"]), ""]
            for t in topics[:2]:
                lines.append(f"📌 **{t['title']}**")
                lines.append(f"🔗 {t['url']}\n")
            return "\n".join(lines), topics
        return (
            f"{GREETING.get(lang, GREETING['tr'])}\n\n"
            f"Forum: {LINKS['forum']}",
            [],
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    user_prompt = (
        f"Kullanici sorusu: {question}\n\n"
        f"Forum bilgi tabani:\n{context}\n\n"
        f"Yukaridaki konulara dayanarak {LANG_NAMES.get(lang, 'Turkce')} dilinde cevap ver. "
        "En alakali konunun tam URL'sini mutlaka ekle."
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _system_prompt(lang)},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=900,
            temperature=0.4,
        )
        answer = response.choices[0].message.content or ""
        return answer.strip(), topics
    except Exception as exc:
        logger.exception("OpenAI hatasi: %s", exc)
        if topics:
            lines = [GREETING.get(lang, GREETING["tr"]), ""]
            for t in topics[:2]:
                lines.append(f"📌 **{t['title']}** — {t['url']}")
            return "\n".join(lines), topics
        return f"Forum: {LINKS['forum']}", []

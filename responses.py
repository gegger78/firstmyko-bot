"""Oyuncuya samimi, cok dilli, dogrudan konu linkli cevaplar."""

from __future__ import annotations

import re

from firstmyko_bot.ai_responder import generate_answer
from firstmyko_bot.config import BRAND_COLOR, LINKS
from firstmyko_bot.faq import match_faq
from firstmyko_bot.forum_search import search_forum_live
from firstmyko_bot.i18n import (
    FOOTER,
    GREETING,
    NO_TOPIC,
    READ_MORE,
    SUMMARY_LABEL,
    TOPIC_FOUND,
    detect_language,
)
from firstmyko_bot.knowledge import search_topics


def _extract_summary(content: str, max_len: int = 350) -> str:
    if not content:
        return ""
    lines: list[str] = []
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("─") or line.startswith("Anahtar Kelimeler"):
            continue
        if line.startswith("FIRSTMYKO —") or line.startswith("FIRSTMYKO -"):
            continue
        lines.append(line)
        if len(" ".join(lines)) > max_len:
            break
    summary = " ".join(lines)
    if len(summary) > max_len:
        summary = summary[: max_len - 3].rsplit(" ", 1)[0] + "..."
    return summary


def _build_embed_dict(
    lang: str,
    question: str,
    body: str,
    topic: dict | None,
    extra_topics: list[dict] | None = None,
) -> dict:
    title = "FIRSTMYKO V1098 Asistan"
    if lang == "en":
        title = "FIRSTMYKO V1098 Assistant"
    elif lang == "es":
        title = "FIRSTMYKO V1098 Asistente"
    elif lang == "ar":
        title = "FIRSTMYKO V1098 مساعد"

    parts = [GREETING[lang], "", body]

    embed: dict = {
        "title": title,
        "description": "\n".join(parts)[:4096],
        "color": BRAND_COLOR,
        "footer": {"text": FOOTER[lang]},
    }

    if topic:
        embed["url"] = topic["url"]
        embed["fields"] = [
            {
                "name": f"📌 {topic['title'][:256]}",
                "value": f"🔗 **{READ_MORE[lang]}:** {topic['url']}",
                "inline": False,
            }
        ]
        summary = _extract_summary(topic.get("content", ""))
        if summary:
            embed["fields"].append(
                {
                    "name": f"💡 {SUMMARY_LABEL[lang]}",
                    "value": summary[:1024],
                    "inline": False,
                }
            )

    if extra_topics:
        links = "\n".join(f"• [{t['title'][:80]}]({t['url']})" for t in extra_topics[:2])
        embed.setdefault("fields", []).append(
            {"name": "📚", "value": links[:1024], "inline": False}
        )

    return embed


def build_player_response(question: str) -> dict:
    """Discord embed dict dondurur."""
    lang = detect_language(question)

    # 1) Hazir FAQ / web / forum kategori eslesmesi
    faq_body, faq_link = match_faq(question)
    if faq_body:
        return _build_embed_dict(lang, question, faq_body, faq_link)

    # 2) Forum konu arama
    local = search_topics(question, limit=5)
    live = search_forum_live(question, limit=5)

    # En iyi eslesmeyi birlestir (canli arama oncelikli)
    seen: set[str] = set()
    topics: list[dict] = []
    for t in live + local:
        url = t.get("url", "")
        if url and url not in seen:
            seen.add(url)
            topics.append(t)

    best = topics[0] if topics else None
    rest = topics[1:3] if len(topics) > 1 else []

    if best:
        summary = _extract_summary(best.get("content", ""), 500)
        body = f"**{TOPIC_FOUND[lang]}**"
        if summary:
            body += f"\n\n{summary}"

        # Guclu eslesme: AI olmadan hizli cevap (kota tasarrufu)
        if summary or not best.get("content"):
            return _build_embed_dict(lang, question, body, best, rest)

        ai_body, _ = generate_answer(question, lang=lang, topics=topics)
        if ai_body and "Forum:" not in ai_body[:30]:
            body = ai_body
        return _build_embed_dict(lang, question, body, best, rest)

    ai_body, ai_topics = generate_answer(question, lang=lang, topics=[])
    if ai_topics:
        return _build_embed_dict(lang, question, ai_body, ai_topics[0], ai_topics[1:3])

    body = (
        f"**{NO_TOPIC[lang]}**\n\n"
        f"🌐 {LINKS['forum']}\n"
        f"📋 {LINKS['yenilikler']}\n"
        f"📖 {LINKS['rehber']}"
    )
    return _build_embed_dict(lang, question, body, None)

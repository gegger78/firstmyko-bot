"""Forum bilgi tabaninda arama ve hizli yonlendirme."""

from __future__ import annotations

import re
import unicodedata

from firstmyko_bot.config import (
    ANNOUNCEMENTS_CHANNEL_ID,
    GIVEAWAY_CHANNEL_ID,
    INTRO_CHANNEL_ID,
    LINKS,
)
from firstmyko_bot.forum_sync import load_knowledge

# Soru kelimeleri aramaya eklenmez; konu eslestirmesi icin esanlamlilar
QUERY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "upgrade": ("upgrade", "anvil", "oran", "basma", "scroll", "arti", "item"),
    "master": ("master", "gorev", "quest", "skill", "level"),
    "skill": ("skill", "stat", "yetenek", "master", "gorev"),
    "cekilis": ("cekilis", "hediye", "giveaway", "odul", "etkinlik"),
    "pus": ("pus", "power", "store", "market", "cash"),
    "party": ("party", "grup", "takim", "lider"),
    "merchant": ("merchant", "pazar", "market", "satis"),
    "minor": ("minor", "assassin", "pot", "combo"),
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", _normalize(text))
    return {w for w in words if len(w) > 2}


def _expand_query_tokens(query_tokens: set[str]) -> set[str]:
    expanded = set(query_tokens)
    for token in list(query_tokens):
        for _key, syns in QUERY_EXPANSIONS.items():
            if token in syns or any(s in token for s in syns if len(s) > 3):
                expanded.update(syns)
    return expanded


def search_topics(query: str, limit: int = 5) -> list[dict]:
    kb = load_knowledge()
    topics = kb.get("topics", [])
    if not topics:
        return []

    query_tokens = _expand_query_tokens(_tokenize(query))
    if not query_tokens:
        return []

    query_norm = _normalize(query)
    scored: list[tuple[float, dict]] = []

    for topic in topics:
        title = topic.get("title", "")
        title_norm = _normalize(title)
        title_tokens = _tokenize(title)
        content_tokens = _tokenize(topic.get("content", "")[:2500])

        overlap = len(query_tokens & (title_tokens | content_tokens))
        title_overlap = len(query_tokens & title_tokens)
        if overlap == 0:
            continue

        score = float(overlap + title_overlap * 4)

        # Baslikta tum onemli kelimeler varsa bonus
        important = [t for t in query_tokens if len(t) > 3]
        if important and all(t in title_norm for t in important[:3]):
            score += 8

        # "upgrade oran" gibi ifadeler
        if "upgrade" in query_norm and "upgrade" in title_norm:
            score += 5
        if "oran" in query_norm and "oran" in title_norm:
            score += 4
        if "master" in query_norm and ("master" in title_norm or "skill" in title_norm):
            score += 4
        if "skill" in query_norm and "skill" in title_norm:
            score += 3

        scored.append((score, topic))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:limit]]


def format_topic_context(topics: list[dict]) -> str:
    if not topics:
        return "Forum bilgi tabaninda eslesen konu bulunamadi."

    blocks = []
    for i, t in enumerate(topics, 1):
        content = t.get("content", "")[:2500]
        blocks.append(
            f"--- KONU {i} ---\n"
            f"Baslik: {t.get('title')}\n"
            f"Forum: {t.get('forum')}\n"
            f"Link: {t.get('url')}\n"
            f"Icerik:\n{content}\n"
        )
    return "\n".join(blocks)


def detect_quick_reply(message: str) -> str | None:
    """Sadece sosyal/cekilis gibi anlik yonlendirmeler (forum aramasi gerektirmez)."""
    text = _normalize(message)

    giveaway_words = ("cekilis", "hediye", "giveaway", "odul")
    if any(w in text for w in giveaway_words):
        lines = [
            "**FIRSTMYKO cekilis ve etkinlikler:**",
            f"Instagram: {LINKS['instagram']}",
            f"WhatsApp: {LINKS['whatsapp']}",
        ]
        if GIVEAWAY_CHANNEL_ID:
            lines.append(f"Discord cekilis kanali: <#{GIVEAWAY_CHANNEL_ID}>")
        return "\n".join(lines)

    if any(w in text for w in ("instagram", "insta", "ig")):
        return f"**Instagram:** {LINKS['instagram']}"
    if any(w in text for w in ("whatsapp", "wp")):
        return f"**WhatsApp:** {LINKS['whatsapp']}"
    if any(w in text for w in ("facebook", "fb")):
        return f"**Facebook:** {LINKS['facebook']}"

    if any(w in text for w in ("duyuru", "announcement", "haber")):
        lines = ["**FIRSTMYKO duyurulari:**"]
        if ANNOUNCEMENTS_CHANNEL_ID:
            lines.append(f"Discord: <#{ANNOUNCEMENTS_CHANNEL_ID}>")
        lines.append(f"Forum: {LINKS['forum']}")
        return "\n".join(lines)

    if any(w in text for w in ("tanitim", "sunucu nedir", "firstmyko nedir")):
        lines = ["**FIRSTMYKO V1098 tanitim:**"]
        if INTRO_CHANNEL_ID:
            lines.append(f"Tanıtım: <#{INTRO_CHANNEL_ID}>")
        lines.append(f"Web: {LINKS['website']}")
        return "\n".join(lines)

    return None


def is_question(message: str) -> bool:
    text = message.strip()
    if not text or len(text) < 4:
        return False
    if text.endswith("?"):
        return True
    starters = (
        "nasıl", "nasil", "nedir", "ne kadar", "nerede", "kaç", "kac", "neler",
        "kim", "hangi", "var mı", "var mi", "ne zaman", "acaba",
        "how", "what", "where", "when", "why", "hello", "help",
        "hola", "como", "que", "donde", "cuando",
    )
    lower = _normalize(text)
    return any(lower.startswith(s) or f" {s}" in lower for s in starters)

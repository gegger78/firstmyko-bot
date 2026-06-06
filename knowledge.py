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


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", _normalize(text))
    return {w for w in words if len(w) > 2}


def search_topics(query: str, limit: int = 5) -> list[dict]:
    kb = load_knowledge()
    topics = kb.get("topics", [])
    if not topics:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[float, dict]] = []
    for topic in topics:
        title_tokens = _tokenize(topic.get("title", ""))
        content_tokens = _tokenize(topic.get("content", "")[:2000])
        overlap = len(query_tokens & (title_tokens | content_tokens))
        title_overlap = len(query_tokens & title_tokens)
        if overlap == 0:
            continue
        score = overlap + title_overlap * 2
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
    """AI kullanmadan hizli cevap gerektiren mesajlar."""
    text = _normalize(message)

    giveaway_words = ("cekilis", "çekiliş", "hediye", "giveaway", "odul", "ödül")
    if any(w in text for w in giveaway_words):
        lines = [
            "**FIRSTMYKO cekilis ve etkinlikler:**",
            f"Instagram: {LINKS['instagram']}",
            f"WhatsApp: {LINKS['whatsapp']}",
        ]
        if GIVEAWAY_CHANNEL_ID:
            lines.append(f"Discord cekilis kanali: <#{GIVEAWAY_CHANNEL_ID}>")
        lines.append(f"\nDetaylar icin forum: {LINKS['forum']}")
        return "\n".join(lines)

    announcement_words = ("duyuru", "announcement", "haber", "acilis", "açılış", "guncelleme", "güncelleme")
    if any(w in text for w in announcement_words):
        lines = ["**FIRSTMYKO duyurulari:**"]
        if ANNOUNCEMENTS_CHANNEL_ID:
            lines.append(f"Discord duyurular: <#{ANNOUNCEMENTS_CHANNEL_ID}>")
        lines.append(f"Forum: {LINKS['forum']}")
        return "\n".join(lines)

    intro_words = ("tanitim", "tanıtım", "sunucu nedir", "firstmyko nedir", "oyun hakkinda", "oyun hakkında")
    if any(w in text for w in intro_words):
        lines = ["**FIRSTMYKO V1098 Old-USKO tanitim:**"]
        if INTRO_CHANNEL_ID:
            lines.append(f"Tanıtım kanali: <#{INTRO_CHANNEL_ID}>")
        lines.append(f"Web: {LINKS['website']}")
        lines.append(f"Forum: {LINKS['forum']}")
        return "\n".join(lines)

    link_map = {
        ("forum", "konu", "rehber"): LINKS["forum"],
        ("web", "site", "indir", "download", "oyunu indir"): LINKS["website"],
        ("instagram", "insta", "ig"): LINKS["instagram"],
        ("facebook", "fb"): LINKS["facebook"],
        ("whatsapp", "wp"): LINKS["whatsapp"],
        ("yenilik", "guncelleme", "update", "ozellik"): LINKS["yenilikler"],
        ("pus", "power up", "powerup", "store", "market"): LINKS["pus"],
        ("upgrade", "anvil", "+ basma", "basma oran"): LINKS["yenilikler"],
    }

    for keywords, url in link_map.items():
        if any(k in text for k in keywords):
            return f"**FIRSTMYKO** — ilgili sayfa:\n{url}\n\nDetayli bilgi: {LINKS['forum']}"

    return None


def is_question(message: str) -> bool:
    text = message.strip()
    if not text or len(text) < 4:
        return False
    if text.endswith("?"):
        return True
    starters = (
        "nasıl", "nasil", "nedir", "ne kadar", "nerede", "kaç", "kac",
        "kim", "hangi", "var mı", "var mi", "ne zaman", "acaba",
        "how", "what", "where", "when", "why",
    )
    lower = _normalize(text)
    return any(lower.startswith(s) or f" {s}" in lower for s in starters)

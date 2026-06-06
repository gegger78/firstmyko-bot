"""Canli forum arama — bilgi tabani bos veya eslesme yoksa."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from firstmyko_bot.config import FORUMS
from firstmyko_bot.knowledge import _normalize, _tokenize

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "FirstMykoDiscordBot/1.0 (+https://firstmyko.net)",
}
BASE = "https://firstmyko.net/"


def _score_title(query_tokens: set[str], title: str) -> float:
    title_norm = _normalize(title)
    title_tokens = _tokenize(title)
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & title_tokens)
    if overlap == 0:
        return 0.0
    score = overlap + overlap / max(len(query_tokens), 1)
    if all(t in title_norm for t in query_tokens if len(t) > 3):
        score += 3
    return score


def search_forum_live(query: str, limit: int = 3) -> list[dict]:
    """Forum kategori sayfalarinda konu basligi tara."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    found: list[tuple[float, dict]] = []
    seen: set[str] = set()

    for forum in FORUMS:
        try:
            resp = requests.get(forum["url"], headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Forum taranamadi %s: %s", forum["url"], exc)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for link in soup.select(".structItem-title a"):
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or not href or "/threads/" not in href:
                continue
            full_url = urljoin(BASE, href)
            if full_url in seen:
                continue
            score = _score_title(query_tokens, title)
            if score <= 0:
                continue
            seen.add(full_url)
            found.append(
                (
                    score,
                    {
                        "title": title,
                        "url": full_url,
                        "forum": forum["name"],
                        "content": "",
                    },
                )
            )

    found.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in found[:limit]]

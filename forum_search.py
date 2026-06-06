"""Canli forum arama — tum kategoriler + konu basliklari."""

from __future__ import annotations

import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from firstmyko_bot.config import FORUMS
from firstmyko_bot.forum_catalog import FORUM_CATEGORIES, forum_url
from firstmyko_bot.knowledge import _expand_query_tokens, _normalize, _tokenize

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "FirstMykoDiscordBot/1.0 (+https://firstmyko.net)",
}
BASE = "https://firstmyko.net/"

# Soru -> forum kategorisi (genel sayfa istendiginde)
CATEGORY_HINTS: list[dict] = [
    {
        "need": {"hata", "cozum"},
        "title": "Hata ve Cozumler",
        "url": forum_url("hata-ve-cozumler.15"),
        "forum": "Hata ve Cozumler",
        "content": "Tum oyun hatalari ve cozum rehberleri.",
    },
    {
        "need": {"master", "skill", "gorev"},
        "title": "Master ve Skill Gorevleri",
        "url": forum_url("master-ve-skill-gorevleri.14"),
        "forum": "Master Gorevleri",
        "content": "Tum class master ve skill gorevleri.",
    },
    {
        "need": {"error", "solution"},
        "title": "Errors and Solutions",
        "url": forum_url("errors-and-solutions-errores-y-soluciones.34"),
        "forum": "Errors and Solutions",
        "content": "English/Spanish error guides.",
    },
]

_forum_cache: list[dict] | None = None
_forum_cache_at: float = 0.0


def _discover_forums() -> list[dict]:
    """Tanimli tum forum kategorileri."""
    global _forum_cache, _forum_cache_at
    if _forum_cache and time.time() - _forum_cache_at < 3600:
        return _forum_cache

    _forum_cache = list(FORUMS)
    _forum_cache_at = time.time()
    return _forum_cache


def _score_match(query_tokens: set[str], query_norm: str, title: str) -> float:
    title_norm = _normalize(title)
    title_tokens = _tokenize(title)
    if not query_tokens:
        return 0.0

    overlap = query_tokens & title_tokens
    if not overlap:
        # Kismi eslesme: "cozumler" ~ "cozum"
        for qt in query_tokens:
            for tt in title_tokens:
                if len(qt) >= 4 and (qt in tt or tt in qt):
                    overlap.add(qt)
        if not overlap:
            return 0.0

    score = len(overlap) * 2 + len(overlap & title_tokens) * 3

    # Baslik neredeyse ayni soru
    if query_norm in title_norm or title_norm in query_norm:
        score += 10

    important = [t for t in query_tokens if len(t) >= 4]
    if important and sum(1 for t in important if t in title_norm) >= len(important):
        score += 6

    return score


def _is_broad_category_query(query_tokens: set[str]) -> bool:
    specific = query_tokens & {
        "dll", "msvcp", "dbghelp", "exe", "directx", "cheat", "upgrade", "pus", "master",
    }
    if specific:
        return False
    has_hata = bool(query_tokens & {"hata", "error", "sorun"})
    has_cozum = bool(query_tokens & {"cozum", "cozumler", "solution", "fix"})
    return has_hata and has_cozum


def _match_category(query_tokens: set[str]) -> dict | None:
    for hint in CATEGORY_HINTS:
        if hint["need"].issubset(query_tokens) or hint["need"] & query_tokens:
            return {
                "title": hint["title"],
                "url": hint["url"],
                "forum": hint["forum"],
                "content": hint["content"],
            }
    return None


def _scrape_forum_threads(forum: dict, query_tokens: set[str], query_norm: str) -> list[tuple[float, dict]]:
    results: list[tuple[float, dict]] = []
    seen: set[str] = set()

    for page in range(1, 4):
        page_url = forum["url"] if page == 1 else f"{forum['url']}page-{page}"
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)
            if resp.status_code == 404:
                break
            resp.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(".structItem-title a")
        if not links:
            break

        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or "/threads/" not in href:
                continue
            full_url = urljoin(BASE, href)
            if full_url in seen:
                continue
            score = _score_match(query_tokens, query_norm, title)
            if score <= 0:
                continue
            seen.add(full_url)
            results.append(
                (
                    score,
                    {
                        "title": title,
                        "url": full_url,
                        "forum": forum.get("name", ""),
                        "content": "",
                    },
                )
            )

    return results


def search_forum_live(query: str, limit: int = 5) -> list[dict]:
    """Tum forum kategorilerinde konu basligi ara."""
    query_norm = _normalize(query)
    raw_tokens = _tokenize(query)
    query_tokens = _expand_query_tokens(raw_tokens)
    if not query_tokens:
        return []

    found: list[tuple[float, dict]] = []

    for forum in _discover_forums():
        found.extend(_scrape_forum_threads(forum, query_tokens, query_norm))

    # Kategori sayfasi — sadece genel sorularda (ornek: "hata ve cozumler")
    category = _match_category(query_tokens)
    if category:
        if _is_broad_category_query(raw_tokens):
            found.append((20.0, category))
        else:
            cat_score = _score_match(query_tokens, query_norm, category["title"]) + 4
            specific = query_tokens & {"dll", "msvcp", "dbghelp", "exe", "directx", "cheat", "dc"}
            best_thread = max((s for s, _ in found), default=0)
            if not specific and cat_score >= best_thread:
                found.append((cat_score, category))

    found.sort(key=lambda x: x[0], reverse=True)

    # Tekrarlayan URL kaldir
    out: list[dict] = []
    seen_urls: set[str] = set()
    for _, topic in found:
        if topic["url"] in seen_urls:
            continue
        seen_urls.add(topic["url"])
        out.append(topic)
        if len(out) >= limit:
            break

    return out

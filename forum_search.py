"""Canli forum arama — yalnizca ilgili kategoriler, paralel istek."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from firstmyko_bot.config import (
    FORUMS,
    LIVE_FORUM_MAX_CATEGORIES,
    LIVE_FORUM_TIMEOUT,
)
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

# Anahtar kelime eslesmezse taranacak varsayilan kategoriler
DEFAULT_FORUM_SLUGS = (
    "firstmyko-oyun-rehberi.37",
    "hata-ve-cozumler.15",
    "yenilikler-ve-detaylari.10",
    "master-ve-skill-gorevleri.14",
)

_forum_cache: list[dict] | None = None
_forum_cache_at: float = 0.0
_forum_by_slug: dict[str, dict] | None = None


def _discover_forums() -> list[dict]:
    """Tanimli tum forum kategorileri."""
    global _forum_cache, _forum_cache_at
    if _forum_cache and time.time() - _forum_cache_at < 3600:
        return _forum_cache

    _forum_cache = list(FORUMS)
    _forum_cache_at = time.time()
    return _forum_cache


def _forums_by_slug() -> dict[str, dict]:
    global _forum_by_slug
    if _forum_by_slug is None:
        _forum_by_slug = {}
        for forum in _discover_forums():
            url = forum.get("url", "")
            for cat in FORUM_CATEGORIES:
                slug = cat["slug"]
                if slug in url:
                    _forum_by_slug[slug] = forum
                    break
    return _forum_by_slug


def _rank_forums_for_query(query_norm: str, query_tokens: set[str], max_forums: int) -> list[dict]:
    """Soruya en uygun birkaç forum kategorisi sec (36 yerine 3-4)."""
    by_slug = _forums_by_slug()
    ranked: list[tuple[float, str]] = []

    for cat in FORUM_CATEGORIES:
        slug = cat["slug"]
        if slug not in by_slug:
            continue
        score = 0.0
        for kw in cat["keywords"]:
            if kw in query_norm:
                score += len(kw.split()) * 3 + 2
            else:
                kw_tokens = _tokenize(kw)
                overlap = query_tokens & kw_tokens
                if overlap:
                    score += len(overlap) * 2

        name_norm = _normalize(cat["name"])
        name_tokens = _tokenize(name_norm)
        score += len(query_tokens & name_tokens) * 1.5

        if score > 0:
            ranked.append((score, slug))

    ranked.sort(key=lambda x: x[0], reverse=True)

    chosen_slugs: list[str] = []
    for _, slug in ranked:
        if slug not in chosen_slugs:
            chosen_slugs.append(slug)
        if len(chosen_slugs) >= max_forums:
            break

    if not chosen_slugs:
        chosen_slugs = list(DEFAULT_FORUM_SLUGS[:max_forums])

    return [by_slug[s] for s in chosen_slugs if s in by_slug]


def _score_match(query_tokens: set[str], query_norm: str, title: str) -> float:
    title_norm = _normalize(title)
    title_tokens = _tokenize(title)
    if not query_tokens:
        return 0.0

    overlap = query_tokens & title_tokens
    if not overlap:
        for qt in query_tokens:
            for tt in title_tokens:
                if len(qt) >= 4 and (qt in tt or tt in qt):
                    overlap.add(qt)
        if not overlap:
            return 0.0

    score = len(overlap) * 2 + len(overlap & title_tokens) * 3

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

    page_url = forum["url"]
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=LIVE_FORUM_TIMEOUT)
        if resp.status_code == 404:
            return results
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("Forum taranamadi %s: %s", page_url, exc)
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.select(".structItem-title a")
    if not links:
        return results

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
    """Iliskili forum kategorilerinde konu basligi ara (hizli mod)."""
    query_norm = _normalize(query)
    raw_tokens = _tokenize(query)
    query_tokens = _expand_query_tokens(raw_tokens)
    if not query_tokens:
        return []

    forums = _rank_forums_for_query(query_norm, query_tokens, LIVE_FORUM_MAX_CATEGORIES)
    found: list[tuple[float, dict]] = []

    workers = min(len(forums), 4)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_scrape_forum_threads, forum, query_tokens, query_norm): forum
            for forum in forums
        }
        for future in as_completed(futures):
            try:
                found.extend(future.result())
            except Exception:
                logger.exception("Canli forum arama hatasi")

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

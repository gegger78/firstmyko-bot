"""FirstMyko forum RSS ve konu iceriklerini senkronize eder."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from html import unescape
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from firstmyko_bot.config import DATA_DIR, FORUMS, KNOWLEDGE_FILE

logger = logging.getLogger(__name__)

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

HEADERS = {
    "User-Agent": "FirstMykoDiscordBot/1.0 (+https://firstmyko.net)",
}


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_thread_full(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        bodies = soup.select(".message-body .bbWrapper")
        if not bodies:
            body = soup.select_one(".bbWrapper")
            return _strip_html(str(body)) if body else ""
        parts = [_strip_html(str(b)) for b in bodies[:3]]
        return "\n\n".join(p for p in parts if p)
    except requests.RequestException as exc:
        logger.warning("Konu cekilemedi %s: %s", url, exc)
        return ""


def _parse_rss(rss_url: str, forum_name: str) -> list[dict]:
    items: list[dict] = []
    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
    except (requests.RequestException, ElementTree.ParseError) as exc:
        logger.error("RSS hatasi %s: %s", rss_url, exc)
        return items

    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_el = item.find("pubDate")
        content_el = item.find("content:encoded", NS)

        title = (title_el.text or "").strip() if title_el is not None else ""
        link = (link_el.text or "").strip() if link_el is not None else ""
        pub_date = (pub_el.text or "").strip() if pub_el is not None else ""
        rss_content = _strip_html(content_el.text or "") if content_el is not None else ""

        if not title or not link:
            continue

        full_content = _fetch_thread_full(link)
        content = full_content if len(full_content) > len(rss_content) else rss_content

        items.append(
            {
                "title": title,
                "url": link,
                "forum": forum_name,
                "pub_date": pub_date,
                "content": content[:8000],
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return items


def sync_forums() -> dict:
    """Tum forumlari cekip knowledge_base.json dosyasina yazar."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_topics: list[dict] = []
    seen_urls: set[str] = set()

    for forum in FORUMS:
        logger.info("Senkron: %s", forum["name"])
        topics = _parse_rss(forum["rss"], forum["name"])
        for topic in topics:
            if topic["url"] in seen_urls:
                continue
            seen_urls.add(topic["url"])
            all_topics.append(topic)

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "topic_count": len(all_topics),
        "topics": all_topics,
    }

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("Senkron tamamlandi: %d konu", len(all_topics))
    return payload


def load_knowledge() -> dict:
    if not KNOWLEDGE_FILE.exists():
        return {"topics": [], "updated_at": None}
    with open(KNOWLEDGE_FILE, encoding="utf-8") as f:
        return json.load(f)

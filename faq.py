"""Hazir cevaplar ve web sitesi link eslestirmesi."""

from __future__ import annotations

import re
import unicodedata

from firstmyko_bot.config import LINKS
from firstmyko_bot.forum_catalog import FORUM_CATEGORIES, forum_url
from firstmyko_bot.i18n import GREETING, detect_language


def _norm(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


# Web sitesi sayfalari
WEB_PAGES: list[dict] = [
    {"keywords": ("indir", "download", "oyunu indir", "client", "kurulum"), "title": "Oyunu Indir", "url": LINKS["indir"]},
    {"keywords": ("kayit", "register", "hesap ac", "uye ol", "kaydol"), "title": "Kayit Ol", "url": LINKS["kayit"]},
    {"keywords": ("baslangic", "starter", "baslangic item", "baslangic itemleri"), "title": "Baslangic Itemleri", "url": LINKS["baslangic"]},
    {"keywords": ("siralama", "rank", "top player", "oyuncu siralama"), "title": "Oyuncu Siralamasi", "url": LINKS["siralama"]},
    {"keywords": ("gunluk gorev", "daily quest", "gunluk quest"), "title": "Gunluk Gorevler", "url": LINKS["gunluk_gorevler"]},
    {"keywords": ("upgrade kayit", "upgrade log", "basma kayit"), "title": "Upgrade Kayitlari", "url": LINKS["upgrade_kayitlari"]},
    {"keywords": ("upgrade oran", "basma oran", "anvil oran"), "title": "Upgrade Oranlari", "url": LINKS["upgrade_oranlari"]},
    {"keywords": ("pus item", "pus fiyat", "cash item", "power up item"), "title": "PUS Itemleri", "url": LINKS["pus_itemleri"]},
    {"keywords": ("kutu drop", "gem drop", "kutu oran", "gem oran"), "title": "Kutu Gem Drop Oranlari", "url": LINKS["kutu_gem"]},
    {"keywords": ("carkifelek", "carki felek", "wheel", "wheel of fun"), "title": "Carkifelek", "url": LINKS["website"]},
]

# Sabit FAQ
FAQ_ENTRIES: list[dict] = [
    {
        "match": ("alt yapi", "altyapi", "empireacs", "empire acs", "infrastructure"),
        "answer_tr": "Oyunumuzun alt yapisi **EMPIREACS** dir.",
        "answer_en": "Our server infrastructure is **EMPIREACS**.",
    },
    {
        "match": ("version", "versiyon", "v1098", "old usko", "hangi version"),
        "answer_tr": "Sunucu surumu: **FIRSTMYKO V1098 Old-USKO Version**.",
        "answer_en": "Server version: **FIRSTMYKO V1098 Old-USKO Version**.",
    },
    {
        "match": ("epin", "e-pin", "bayi", "haydar", "kc al", "cash al"),
        "answer_tr": f"Resmi E-PIN bayimiz: **Haydar Game**\n{LINKS['epin_bayi']}",
        "answer_en": f"Official E-PIN dealer: **Haydar Game**\n{LINKS['epin_bayi']}",
    },
    {
        "match": ("cekilis kazandim", "cekilisi kazandim", "odul kazandim", "hediye kazandim", "won giveaway"),
        "answer_tr": (
            "Tebrikler! Lutfen **oyun ici nick** ve **kullanici adinizi** "
            "yetkililere veya cekilis kanalina iletin."
        ),
        "answer_en": "Congratulations! Please share your **in-game nick** and **account name** with staff.",
    },
    {
        "match": (
            "carkifelek", "carki felek", "carkifeleg", "wheel of fun",
            "carkifelek var", "carkifelek mevcut", "carkifelek wam",
        ),
        "answer_tr": (
            f"Evet, **Carkifelek (Wheel of Fun)** mevcuttur!\n"
            f"Web sitemizden ulasabilirsiniz: {LINKS['website']}\n"
            f"Detaylar: {LINKS['eventler']}"
        ),
        "answer_en": (
            f"Yes! **Wheel of Fun** is available!\n"
            f"Visit: {LINKS['website']}\n"
            f"Events: {LINKS['eventler']}"
        ),
        "link": {"title": "Carkifelek / Wheel of Fun", "url": LINKS["website"], "forum": "Web", "content": ""},
    },
    {
        "match": ("oyun ici soru", "ticket", "destek talebi", "sorunum var", "yardim lazim yetkili"),
        "answer_tr": "Oyun ici sorunlariniz icin lutfen **Ticket** aciniz. Yetkililer en kisa surede donus yapacaktir.",
        "answer_en": "For in-game issues, please open a **Support Ticket**. Staff will respond shortly.",
    },
]


def _match_forum_category(text: str) -> dict | None:
    best: tuple[float, dict] | None = None
    for cat in FORUM_CATEGORIES:
        score = 0.0
        for kw in cat["keywords"]:
            if kw in text:
                score += len(kw.split()) * 2 + 1
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, cat)
    if not best:
        return None
    cat = best[1]
    return {
        "title": cat["name"],
        "url": forum_url(cat["slug"]),
        "forum": cat["name"],
        "content": "",
    }


def _match_web_page(text: str) -> dict | None:
    for page in WEB_PAGES:
        if any(kw in text for kw in page["keywords"]):
            return {"title": page["title"], "url": page["url"], "forum": "Web Sitesi", "content": ""}
    return None


def match_faq(message: str) -> tuple[str | None, dict | None]:
    """
    Hazir FAQ veya dogrudan link eslesmesi.
    Donus: (cevap metni veya None, konu/link dict veya None)
    """
    text = _norm(message)
    lang = detect_language(message)
    greeting = GREETING.get(lang, GREETING["tr"])

    # Carkifelek: yazim hatalari (wamri, varmi) FAQ'ye gitmeli, yenilikler degil
    if "carkifelek" in text or "carki felek" in text or (
        "carki" in text and any(x in text for x in ("var", "wam", "mevcut", "wheel"))
    ):
        for entry in FAQ_ENTRIES:
            if "carkifelek" in entry["match"]:
                body = entry.get(f"answer_{lang}") or entry["answer_tr"]
                link = entry.get("link")
                return f"{greeting}\n\n{body}", link

    for entry in FAQ_ENTRIES:
        if any(m in text for m in entry["match"]):
            body = entry.get(f"answer_{lang}") or entry["answer_tr"]
            link = entry.get("link")
            return f"{greeting}\n\n{body}", link

    web = _match_web_page(text)
    if web:
        return (
            f"{greeting}\n\n**{web['title']}** sayfasina yonlendiriyorum:",
            web,
        )

    forum = _match_forum_category(text)
    if forum:
        return (
            f"{greeting}\n\n**{forum['title']}** forum bolumu:",
            forum,
        )

    return None, None

"""Tum firstmyko.net forum kategorileri ve anahtar kelimeler."""

from __future__ import annotations

BASE = "https://firstmyko.net/index.php?forums/"

# slug, gorunen ad, eslesme kelimeleri
FORUM_CATEGORIES: list[dict] = [
    {"slug": "duyurular.9", "name": "Duyurular", "keywords": ("duyuru", "announcement", "haber", "anuncio")},
    {"slug": "firstmyko-oyun-rehberi.37", "name": "FIRSTMYKO Oyun Rehberi", "keywords": ("oyun rehberi", "rehber", "guide")},
    {"slug": "yenilikler-ve-detaylari.10", "name": "Yenilikler ve Detaylari", "keywords": ("yenilik", "detay", "guncelleme", "update", "ozellik")},
    {"slug": "gunluk-collection-race-etkinlikleri.25", "name": "Gunluk Collection Race", "keywords": ("collection race", "gunluk collection", "cr event")},
    {"slug": "oyun-ici-eventler.11", "name": "Oyun Ici Eventler", "keywords": ("event", "etkinlik", "chaos", "lottery", "war event", "cz event")},
    {"slug": "power-up-store.12", "name": "Power UP Store (TR)", "keywords": ("pus", "power up store", "cash", "market")},
    {"slug": "sosyal-medya-etkinlikleri.13", "name": "Sosyal Medya Etkinlikleri", "keywords": ("sosyal medya", "instagram etkinlik", "facebook etkinlik")},
    {"slug": "master-ve-skill-gorevleri.14", "name": "Master ve Skill Gorevleri", "keywords": ("master gorev", "skill gorev", "master ve skill")},
    {"slug": "mage-master-skill-gorevleri.43", "name": "Mage Master & Skill", "keywords": ("mage master", "mage skill", "mage gorev", "blink mage")},
    {"slug": "priest-master-skill-gorevleri.42", "name": "Priest Master & Skill", "keywords": ("priest master", "priest skill", "judgment", "priest gorev")},
    {"slug": "rogue-master-skill-gorevleri.41", "name": "Rogue Master & Skill", "keywords": ("rogue master", "rogue skill", "assassin master", "magic shield scroll")},
    {"slug": "warrior-master-skill-gorevleri.39", "name": "Warrior Master & Skill", "keywords": ("warrior master", "warrior skill", "berserking", "scream scroll")},
    {"slug": "hata-ve-cozumler.15", "name": "Hata ve Cozumler", "keywords": ("hata", "cozum", "error", "sorun", "dll", "dc hatasi", "cheat detected")},
    {"slug": "tekrarlanabilir-haftalik-ve-gunluk-gorevler.22", "name": "Haftalik ve Gunluk Gorevler", "keywords": ("gunluk gorev", "haftalik gorev", "quest", "gorevler")},
    {"slug": "clan-oyuncu-tanitim-clan-player-introductions.17", "name": "Clan & Oyuncu Tanitim", "keywords": ("clan tanitim", "oyuncu tanitim", "introduction")},
    {"slug": "pazar-alani-marketplace-mercado.18", "name": "Pazar Alani", "keywords": ("pazar", "marketplace", "al sat", "ticaret")},
    {"slug": "resim-video-paylasimi.19", "name": "Resim & Video", "keywords": ("resim", "video", "ss", "screenshot")},
    {"slug": "oyuncu-mahkemesi.20", "name": "Oyuncu Mahkemesi", "keywords": ("mahkeme", "sikayet", "report")},
    {"slug": "oneriler.21", "name": "Oneriler", "keywords": ("oneri", "suggestion", "fikir")},
    {"slug": "innovations-and-details.40", "name": "Innovations and Details (EN)", "keywords": ("innovation", "innovations and details")},
    {"slug": "firstmyko-new-server-introduction-click-here.7", "name": "Server Introduction (EN/ES)", "keywords": ("server introduction", "new server", "tanitim ingilizce")},
    {"slug": "announcements-anuncios.27", "name": "Announcements/Anuncios", "keywords": ("announcements", "anuncios")},
    {"slug": "firstmyko-game-guide.38", "name": "FIRSTMYKO Game Guide (EN)", "keywords": ("game guide", "boss respawn", "draki", "tattoo", "genie guide")},
    {"slug": "updates-and-details-novedades-y-detalles.28", "name": "Updates and Details (EN/ES)", "keywords": ("updates and details", "novedades")},
    {"slug": "daily-collection-race-events.29", "name": "Daily Collection Race (EN)", "keywords": ("daily collection race",)},
    {"slug": "in-game-events-eventos-del-juego.30", "name": "In-Game Events (EN/ES)", "keywords": ("in-game events", "eventos del juego")},
    {"slug": "power-up-store.31", "name": "Power UP Store (EN)", "keywords": ("pus english", "power up store en")},
    {"slug": "social-media-events-eventos-en-redes-sociales.32", "name": "Social Media Events", "keywords": ("social media events", "redes sociales")},
    {"slug": "master-and-skill-quests.33", "name": "Master and Skill Quests (EN)", "keywords": ("master and skill quests", "master quest english")},
    {"slug": "warrior-master-skill-quests.47", "name": "Warrior Master Quests (EN)", "keywords": ("warrior master quest", "ground slam", "berserking en")},
    {"slug": "rogue-master-skill-quests.46", "name": "Rogue Master Quests (EN)", "keywords": ("rogue master quest",)},
    {"slug": "priest-master-skill-quests.45", "name": "Priest Master Quests (EN)", "keywords": ("priest master quest",)},
    {"slug": "mage-master-skill-quests.44", "name": "Mage Master Quests (EN)", "keywords": ("mage master quest", "mage blink en")},
    {"slug": "repeatable-weekly-and-daily-quests.35", "name": "Weekly/Daily Quests (EN)", "keywords": ("weekly quest", "daily quest en", "repeatable quest")},
    {"slug": "suggestions-sugerencias.36", "name": "Suggestions/Sugerencias", "keywords": ("suggestions", "sugerencias")},
    {"slug": "errors-and-solutions-errores-y-soluciones.34", "name": "Errors and Solutions (EN/ES)", "keywords": ("errors and solutions", "errores y soluciones", "error solution")},
]


def forum_url(slug: str) -> str:
    return f"{BASE}{slug}/"


def forum_rss(slug: str) -> str:
    return f"{BASE}{slug}/index.rss"


def build_forums_sync_list() -> list[dict]:
    """forum_sync.py icin RSS listesi."""
    out: list[dict] = []
    seen: set[str] = set()
    for cat in FORUM_CATEGORIES:
        slug = cat["slug"]
        if slug in seen:
            continue
        seen.add(slug)
        out.append(
            {
                "id": slug.split(".")[-1],
                "name": cat["name"],
                "url": forum_url(slug),
                "rss": forum_rss(slug),
            }
        )
    return out

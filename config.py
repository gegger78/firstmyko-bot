import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_int(key: str, default: int = 0) -> int:
    val = (os.getenv(key) or "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(key: str, default: float = 2.0) -> float:
    val = (os.getenv(key) or "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge_base.json"

# Discord
DISCORD_BOT_TOKEN = (os.getenv("DISCORD_BOT_TOKEN") or "").strip()
WELCOME_CHANNEL_ID = _env_int("WELCOME_CHANNEL_ID")
GENERAL_CHAT_CHANNEL_ID = _env_int("GENERAL_CHAT_CHANNEL_ID")
GIVEAWAY_CHANNEL_ID = _env_int("GIVEAWAY_CHANNEL_ID")
ANNOUNCEMENTS_CHANNEL_ID = _env_int("ANNOUNCEMENTS_CHANNEL_ID")
INTRO_CHANNEL_ID = _env_int("INTRO_CHANNEL_ID")
ADMIN_ROLE_ID = _env_int("ADMIN_ROLE_ID")

# OpenAI (yapay zeka cevaplar)
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
AI_ENABLED = bool(OPENAI_API_KEY)

# Forum senkron
FORUM_SYNC_INTERVAL_HOURS = max(_env_float("FORUM_SYNC_INTERVAL_HOURS", 2.0), 0.25)

# Linkler
LINKS = {
    "forum": "https://firstmyko.net/",
    "website": "https://firstmyko.com/",
    "instagram": "https://www.instagram.com/firstmyko/",
    "facebook": "https://www.facebook.com/FirstMykoo",
    "whatsapp": "https://chat.whatsapp.com/LEL6u1kq8bMLpmi8UubOEt",
    "yenilikler": "https://firstmyko.net/index.php?forums/yenilikler-ve-detaylari.10/",
    "pus": "https://firstmyko.net/index.php?forums/power-up-store.12/",
    "rehber": "https://firstmyko.net/index.php?forums/firstmyko-oyun-rehberi.37/",
}

FORUMS = [
    {
        "id": "10",
        "name": "Yenilikler ve Detayları",
        "url": LINKS["yenilikler"],
        "rss": "https://firstmyko.net/index.php?forums/yenilikler-ve-detaylari.10/index.rss",
    },
    {
        "id": "12",
        "name": "Power UP Store",
        "url": LINKS["pus"],
        "rss": "https://firstmyko.net/index.php?forums/power-up-store.12/index.rss",
    },
    {
        "id": "37",
        "name": "FİRSTMYKO OYUN REHBERİ",
        "url": LINKS["rehber"],
        "rss": "https://firstmyko.net/index.php?forums/firstmyko-oyun-rehberi.37/index.rss",
    },
]

BRAND_COLOR = 0x44F880

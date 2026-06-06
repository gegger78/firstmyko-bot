import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge_base.json"

# Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0") or "0")
GENERAL_CHAT_CHANNEL_ID = int(os.getenv("GENERAL_CHAT_CHANNEL_ID", "0") or "0")
GIVEAWAY_CHANNEL_ID = int(os.getenv("GIVEAWAY_CHANNEL_ID", "0") or "0")
ANNOUNCEMENTS_CHANNEL_ID = int(os.getenv("ANNOUNCEMENTS_CHANNEL_ID", "0") or "0")
INTRO_CHANNEL_ID = int(os.getenv("INTRO_CHANNEL_ID", "0") or "0")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0") or "0")

# OpenAI (yapay zeka cevaplar)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
AI_ENABLED = bool(OPENAI_API_KEY)

# Forum senkron
FORUM_SYNC_INTERVAL_HOURS = float(os.getenv("FORUM_SYNC_INTERVAL_HOURS", "2"))

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

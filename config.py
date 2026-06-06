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

# Yapay zeka (OpenAI veya Google Gemini)
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
AI_PROVIDER = (os.getenv("AI_PROVIDER") or "auto").strip().lower()

if AI_PROVIDER == "gemini":
    AI_ENGINE = "gemini" if GEMINI_API_KEY else None
elif AI_PROVIDER == "openai":
    AI_ENGINE = "openai" if OPENAI_API_KEY else None
else:
    # auto: Gemini oncelikli (ucretsiz kota genelde daha uygun)
    if GEMINI_API_KEY:
        AI_ENGINE = "gemini"
    elif OPENAI_API_KEY:
        AI_ENGINE = "openai"
    else:
        AI_ENGINE = None

AI_ENABLED = AI_ENGINE is not None

# Forum senkron
FORUM_SYNC_INTERVAL_HOURS = max(_env_float("FORUM_SYNC_INTERVAL_HOURS", 2.0), 0.25)

from firstmyko_bot.forum_catalog import build_forums_sync_list

# Linkler
LINKS = {
    "forum": "https://firstmyko.net/",
    "website": "https://firstmyko.com/",
    "instagram": "https://www.instagram.com/firstmyko/",
    "facebook": "https://www.facebook.com/FirstMykoo",
    "whatsapp": "https://chat.whatsapp.com/LEL6u1kq8bMLpmi8UubOEt",
    "epin_bayi": "https://www.haydargame.com/",
    # Web sitesi sayfalari
    "indir": "https://firstmyko.com/indir",
    "kayit": "https://firstmyko.com/kayit",
    "baslangic": "https://firstmyko.com/baslangic",
    "siralama": "https://firstmyko.com/siralamalar/oyuncu",
    "gunluk_gorevler": "https://firstmyko.com/oyuncu-rehberi/gunluk-gorevler",
    "upgrade_kayitlari": "https://firstmyko.com/oyuncu-rehberi/upgrade-kayitlari",
    "upgrade_oranlari": "https://firstmyko.com/oyuncu-rehberi/upgrade-oranlari",
    "pus_itemleri": "https://firstmyko.com/oyuncu-rehberi/pus-itemleri",
    "kutu_gem": "https://firstmyko.com/oyuncu-rehberi/kutu-gem-droplari",
    # Forum kategorileri (one cikan)
    "duyurular": "https://firstmyko.net/index.php?forums/duyurular.9/",
    "yenilikler": "https://firstmyko.net/index.php?forums/yenilikler-ve-detaylari.10/",
    "eventler": "https://firstmyko.net/index.php?forums/oyun-ici-eventler.11/",
    "pus": "https://firstmyko.net/index.php?forums/power-up-store.12/",
    "rehber": "https://firstmyko.net/index.php?forums/firstmyko-oyun-rehberi.37/",
    "master_gorev": "https://firstmyko.net/index.php?forums/master-ve-skill-gorevleri.14/",
    "hata_cozum": "https://firstmyko.net/index.php?forums/hata-ve-cozumler.15/",
    "hata_en": "https://firstmyko.net/index.php?forums/errors-and-solutions-errores-y-soluciones.34/",
    "game_guide_en": "https://firstmyko.net/index.php?forums/firstmyko-game-guide.38/",
}

FORUMS = build_forums_sync_list()

BRAND_COLOR = 0x44F880

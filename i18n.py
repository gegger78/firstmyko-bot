"""Dil algilama ve cok dilli sabit metinler (TR, EN, ES, AR)."""

from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"

    norm = _normalize(text)
    if any(c in text for c in "ğıüşöçİĞÜŞÖÇ"):
        return "tr"

    es_markers = (
        "hola", "como", "qué", "que ", "donde", "cuando", "precio",
        "ayuda", "gracias", "cuanto", "servidor", "juego", "novedades",
    )
    en_markers = (
        "hello", "how ", "what ", "where ", "when ", "help", "please",
        "upgrade rate", "rates", "server", "guide", "download",
    )
    tr_markers = (
        "neler", "nedir", "nasil", "nasıl", "merhaba", "oran", "gorev",
        "görev", "cekilis", "sunucu", "oyun", "yardim", "yardım",
    )

    es = sum(1 for w in es_markers if w in norm)
    en = sum(1 for w in en_markers if w in norm)
    tr = sum(1 for w in tr_markers if w in norm)

    if en >= es and en >= tr and en > 0:
        return "en"
    if es > tr and es > 0:
        return "es"
    return "tr"


GREETING: dict[str, str] = {
    "tr": (
        "Merhaba! **Size hemen yardimci oluyorum!** 🌟\n"
        "**FIRSTMYKO V1098 Old-USKO** ailesine hos geldiniz!"
    ),
    "en": (
        "Hello! **I'm here to help you right away!** 🌟\n"
        "Welcome to **FIRSTMYKO V1098 Old-USKO**!"
    ),
    "es": (
        "Hola! **Estoy aqui para ayudarte de inmediato!** 🌟\n"
        "Bienvenido a **FIRSTMYKO V1098 Old-USKO**!"
    ),
    "ar": (
        "مرحباً! **أنا هنا لمساعدتك فوراً!** 🌟\n"
        "أهلاً بك في **FIRSTMYKO V1098 Old-USKO**!"
    ),
}

TOPIC_FOUND: dict[str, str] = {
    "tr": "Forumda tam konuyu buldum — asagidaki linke tiklayin:",
    "en": "I found the exact forum topic — click the link below:",
    "es": "Encontre el tema exacto en el foro — haz clic en el enlace:",
    "ar": "وجدت الموضوع الدقيق في المنتدى — انقر على الرابط:",
}

READ_MORE: dict[str, str] = {
    "tr": "Tam detaylar icin",
    "en": "Full details at",
    "es": "Detalles completos en",
    "ar": "التفاصيل الكاملة في",
}

NO_TOPIC: dict[str, str] = {
    "tr": "Bu konu icin forumumuzu incelemenizi oneririz:",
    "en": "For this topic, please check our forum:",
    "es": "Para este tema, consulta nuestro foro:",
    "ar": "لهذا الموضوع، يرجى زيارة منتدانا:",
}

SUMMARY_LABEL: dict[str, str] = {
    "tr": "Ozet",
    "en": "Summary",
    "es": "Resumen",
    "ar": "ملخص",
}

FOOTER: dict[str, str] = {
    "tr": "FIRSTMYKO V1098 | TR · EN · ES · AR desteklenir",
    "en": "FIRSTMYKO V1098 | TR · EN · ES · AR supported",
    "es": "FIRSTMYKO V1098 | TR · EN · ES · AR disponibles",
    "ar": "FIRSTMYKO V1098 | TR · EN · ES · AR مدعومة",
}

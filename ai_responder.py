"""OpenAI ile forum bilgisi destekli cevap uretimi."""

from __future__ import annotations

import logging

from openai import OpenAI

from firstmyko_bot.config import AI_ENABLED, LINKS, OPENAI_API_KEY, OPENAI_MODEL
from firstmyko_bot.knowledge import format_topic_context, search_topics

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Sen FIRSTMYKO V1098 Old-USKO Knight Online sunucusunun resmi Discord asistanisin.
Sunucu adi: FIRSTMYKO V1098 Old-USKO Version

Gorevlerin:
1. Oyuncularin sorularini Turkce, samimi ve profesyonel sekilde yanitla.
2. Cevaplari SADECE sana verilen forum bilgi tabanindaki iceriklere dayandir.
3. Bilgi tabaninda net cevap yoksa tahmin etme; forum linkine yonlendir.
4. Oyun disi konularda kibarca FIRSTMYKO ile ilgili sorulara odaklan.
5. Kisa ve okunabilir yaz (Discord icin uygun, max ~1200 karakter).

Resmi linkler:
- Forum: {forum}
- Web sitesi: {website}
- Instagram: {instagram}
- Facebook: {facebook}
- WhatsApp: {whatsapp}
- Yenilikler: {yenilikler}
- Power UP Store: {pus}
- Oyun Rehberi: {rehber}

Cevabinin sonuna mutlaka en alakali forum konusu linkini ekle.
Birden fazla konu uygunsa en onemli 1-2 link ver.
""".format(**LINKS)


def generate_answer(question: str) -> tuple[str, list[dict]]:
    topics = search_topics(question, limit=5)
    context = format_topic_context(topics)

    if not AI_ENABLED:
        if topics:
            lines = [
                "**Forumda buldugum konular:**",
                "",
            ]
            for t in topics[:3]:
                lines.append(f"• **{t['title']}** — {t['url']}")
            lines.append(f"\nTum detaylar: {LINKS['forum']}")
            return "\n".join(lines), topics

        return (
            f"Bu soru icin forumumuzu incelemenizi oneririz:\n{LINKS['forum']}\n\n"
            f"Yenilikler: {LINKS['yenilikler']}\n"
            f"Rehber: {LINKS['rehber']}",
            [],
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    user_prompt = (
        f"Kullanici sorusu: {question}\n\n"
        f"Forum bilgi tabani (guncel):\n{context}\n\n"
        "Yukaridaki bilgilere dayanarak cevap ver."
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=900,
            temperature=0.4,
        )
        answer = response.choices[0].message.content or ""
        return answer.strip(), topics
    except Exception as exc:
        logger.exception("OpenAI hatasi: %s", exc)
        if topics:
            return (
                f"AI gecici olarak kullanilamiyor. Ilgili forum konulari:\n"
                + "\n".join(f"• {t['title']}: {t['url']}" for t in topics[:3]),
                topics,
            )
        return f"Sorunuz icin forumu ziyaret edin: {LINKS['forum']}", []

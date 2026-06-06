"""
FIRSTMYKO V1098 — Resmi Discord Botu
- Yeni uyeleri karsilar
- Sorulari AI + forum bilgi tabani ile yanitlar
- Forum otomatik senkron
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

from firstmyko_bot.config import (
    ADMIN_ROLE_ID,
    AI_ENABLED,
    ANNOUNCEMENTS_CHANNEL_ID,
    BRAND_COLOR,
    DISCORD_BOT_TOKEN,
    FORUM_SYNC_INTERVAL_HOURS,
    GENERAL_CHAT_CHANNEL_ID,
    GIVEAWAY_CHANNEL_ID,
    INTRO_CHANNEL_ID,
    LINKS,
    WELCOME_CHANNEL_ID,
)
from firstmyko_bot.forum_sync import load_knowledge, sync_forums
from firstmyko_bot.knowledge import detect_quick_reply, is_question
from firstmyko_bot.responses import build_player_response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("firstmyko_bot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Kullanici basina cooldown (saniye)
USER_COOLDOWN: dict[int, float] = {}
COOLDOWN_SECONDS = 15


def _welcome_channel(guild: discord.Guild) -> discord.TextChannel | None:
    if WELCOME_CHANNEL_ID:
        ch = guild.get_channel(WELCOME_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
    if GENERAL_CHAT_CHANNEL_ID:
        ch = guild.get_channel(GENERAL_CHAT_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            return ch
    for ch in guild.text_channels:
        if ch.name in ("genel", "general", "genel-sohbet", "sohbet", "chat"):
            return ch
    return guild.system_channel


def _is_admin(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    if ADMIN_ROLE_ID and any(r.id == ADMIN_ROLE_ID for r in member.roles):
        return True
    return False


def _on_cooldown(user_id: int) -> bool:
    now = datetime.now(timezone.utc).timestamp()
    last = USER_COOLDOWN.get(user_id, 0)
    if now - last < COOLDOWN_SECONDS:
        return True
    USER_COOLDOWN[user_id] = now
    return False


def _start_health_server(port: int) -> None:
    """Render/Fly icin HTTP saglik kontrolu (Discord baglanmadan once baslar)."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"FIRSTMYKO Bot OK")

        def log_message(self, *_args) -> None:
            pass

    def run() -> None:
        server = HTTPServer(("0.0.0.0", port), Handler)
        logger.info("Health server port %s", port)
        server.serve_forever()

    threading.Thread(target=run, daemon=True).start()


@bot.event
async def on_ready() -> None:
    logger.info("Bot hazir: %s (ID: %s)", bot.user, bot.user.id if bot.user else "?")
    if not forum_sync_loop.is_running():
        forum_sync_loop.start()

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="FIRSTMYKO V1098 | !yardim",
        )
    )


@bot.event
async def on_member_join(member: discord.Member) -> None:
    channel = _welcome_channel(member.guild)
    if not channel:
        return

    embed = discord.Embed(
        title="FIRSTMYKO V1098'a Hos Geldin!",
        description=(
            f"Merhaba {member.mention}! **FIRSTMYKO V1098 Old-USKO** ailesine katildin.\n\n"
            "Sorularin icin bu kanalda yazabilir veya `!yardim` kullanabilirsin.\n"
            "Oyun rehberleri ve yenilikler icin forumumuzu ziyaret et!"
        ),
        color=BRAND_COLOR,
    )
    embed.add_field(name="Forum", value=f"[firstmyko.net]({LINKS['forum']})", inline=True)
    embed.add_field(name="Web", value=f"[firstmyko.com]({LINKS['website']})", inline=True)
    embed.add_field(name="Instagram", value=f"[@firstmyko]({LINKS['instagram']})", inline=True)
    if INTRO_CHANNEL_ID:
        embed.add_field(name="Tanıtım", value=f"<#{INTRO_CHANNEL_ID}>", inline=True)
    if ANNOUNCEMENTS_CHANNEL_ID:
        embed.add_field(name="Duyurular", value=f"<#{ANNOUNCEMENTS_CHANNEL_ID}>", inline=True)
    embed.set_footer(text="FIRSTMYKO V1098 Old-USKO | Resmi Discord Botu")

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        logger.warning("Karsilama mesaji gonderilemedi: %s", channel.name)


@bot.command(name="yardim", aliases=["help", "komutlar"])
async def cmd_help(ctx: commands.Context) -> None:
    embed = discord.Embed(
        title="FIRSTMYKO Bot — Komutlar",
        description="Oyun ve sunucu hakkinda sorularini yazman yeterli!",
        color=BRAND_COLOR,
    )
    embed.add_field(name="!yardim", value="Bu mesaji gosterir", inline=False)
    embed.add_field(name="!linkler", value="Tum resmi linkler", inline=False)
    embed.add_field(name="!forum", value="Forum ana sayfa", inline=False)
    embed.add_field(name="!senkron", value="(Admin) Forum bilgisini guncelle", inline=False)
    embed.add_field(
        name="Soru sorma",
        value=(
            "Genel sohbette soru sor (ornek: *upgrade oranlari nelerdir?*)\n"
            "Bot forumdan tam konu linkini gonderir.\n"
            "**Diller:** Turkce, English, Espanol, Arabic"
        ),
        inline=False,
    )
    ai_status = "Aktif (OpenAI)" if AI_ENABLED else "Kapali — OPENAI_API_KEY ekleyin"
    embed.set_footer(text=f"AI: {ai_status}")
    await ctx.send(embed=embed)


@bot.command(name="linkler", aliases=["links"])
async def cmd_links(ctx: commands.Context) -> None:
    embed = discord.Embed(title="FIRSTMYKO Resmi Linkler", color=BRAND_COLOR)
    embed.add_field(name="Forum", value=LINKS["forum"], inline=False)
    embed.add_field(name="Web Sitesi", value=LINKS["website"], inline=False)
    embed.add_field(name="Instagram", value=LINKS["instagram"], inline=False)
    embed.add_field(name="Facebook", value=LINKS["facebook"], inline=False)
    embed.add_field(name="WhatsApp", value=LINKS["whatsapp"], inline=False)
    embed.add_field(name="Yenilikler", value=LINKS["yenilikler"], inline=False)
    embed.add_field(name="Power UP Store", value=LINKS["pus"], inline=False)
    embed.add_field(name="Oyun Rehberi", value=LINKS["rehber"], inline=False)
    if INTRO_CHANNEL_ID:
        embed.add_field(name="Firstmyko Tanitim", value=f"<#{INTRO_CHANNEL_ID}>", inline=False)
    if ANNOUNCEMENTS_CHANNEL_ID:
        embed.add_field(name="Duyurular", value=f"<#{ANNOUNCEMENTS_CHANNEL_ID}>", inline=False)
    if GIVEAWAY_CHANNEL_ID:
        embed.add_field(name="Cekilis Kanali", value=f"<#{GIVEAWAY_CHANNEL_ID}>", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="forum")
async def cmd_forum(ctx: commands.Context) -> None:
    await ctx.send(
        f"**FIRSTMYKO Resmi Forum:** {LINKS['forum']}\n"
        f"Yenilikler: {LINKS['yenilikler']}\n"
        f"Rehber: {LINKS['rehber']}"
    )


@bot.command(name="senkron", aliases=["sync"])
@commands.has_permissions(administrator=True)
async def cmd_sync(ctx: commands.Context) -> None:
    msg = await ctx.send("Forum senkronize ediliyor...")
    result = await asyncio.to_thread(sync_forums)
    await msg.edit(content=f"Senkron tamamlandi: **{result['topic_count']}** konu kaydedildi.")


@bot.command(name="bilgi")
async def cmd_info(ctx: commands.Context) -> None:
    kb = load_knowledge()
    updated = kb.get("updated_at", "Henuz yok")
    count = kb.get("topic_count", len(kb.get("topics", [])))
    await ctx.send(
        f"Forum bilgi tabani: **{count}** konu\n"
        f"Son guncelleme: `{updated}`\n"
        f"Otomatik senkron: her **{FORUM_SYNC_INTERVAL_HOURS}** saat"
    )


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith("!"):
        return

    # Sadece genel sohbet kanalinda otomatik cevap (ayarliysa)
    if GENERAL_CHAT_CHANNEL_ID and message.channel.id != GENERAL_CHAT_CHANNEL_ID:
        return

    mentioned = bot.user and bot.user in message.mentions
    quick = detect_quick_reply(message.content)
    # Soru degilse bile "yenilik", "pus", "cekilis" gibi anahtar kelimelerde cevap ver
    should_reply = is_question(message.content) or mentioned or bool(quick)

    if not should_reply:
        return

    if _on_cooldown(message.author.id):
        return

    if quick:
        await message.reply(quick, mention_author=False)
        return

    async with message.channel.typing():
        embed_data = await asyncio.to_thread(build_player_response, message.content)

    embed = discord.Embed.from_dict(embed_data)

    try:
        await message.reply(embed=embed, mention_author=False)
    except discord.HTTPException:
        await message.channel.send(embed=embed)


@tasks.loop(hours=FORUM_SYNC_INTERVAL_HOURS)
async def forum_sync_loop() -> None:
    logger.info("Otomatik forum senkronu basliyor...")
    try:
        result = await asyncio.to_thread(sync_forums)
        logger.info("Senkron OK: %d konu", result["topic_count"])
    except Exception:
        logger.exception("Forum senkron hatasi")


@forum_sync_loop.before_loop
async def before_sync() -> None:
    await bot.wait_until_ready()
    logger.info("Ilk forum senkronu...")
    await asyncio.to_thread(sync_forums)


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    port = int((os.getenv("PORT") or "0").strip() or "0")
    if port > 0:
        _start_health_server(port)
        print(f"[OK] Health server port {port}")

    if not DISCORD_BOT_TOKEN:
        print("\n[HATA] DISCORD_BOT_TOKEN eksik! Render -> Environment -> ekle\n")
        sys.exit(1)

    if DISCORD_BOT_TOKEN.count(".") != 2:
        print("\n[HATA] Token formati hatali (3 parca olmali). Developer Portal -> Reset Token\n")
        sys.exit(1)

    print("[OK] Token yuklendi, Discord'a baglaniliyor...")

    # Baglanti testi sadece yerel Windows icin (Render/Linux'ta atla)
    if sys.platform == "win32" and not os.getenv("SKIP_DISCORD_CHECK"):
        try:
            import requests
            requests.get("https://discord.com/api/v10/gateway", timeout=10)
        except requests.exceptions.RequestException:
            print("\n[HATA] Bilgisayariniz discord.com'a baglanamiyor.")
            print("       Bulutta calistir (Render) veya VPN/antivirus dene.\n")
            sys.exit(1)

    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("\n[HATA] Gecersiz bot token. Developer Portal -> Reset Token\n")
        sys.exit(1)
    except discord.PrivilegedIntentsRequired:
        print("\n[HATA] Privileged Intent acilmamis!")
        print(" Discord Developer Portal -> Bot -> Privileged Gateway Intents:")
        print("   1. SERVER MEMBERS INTENT  -> AC")
        print("   2. MESSAGE CONTENT INTENT -> AC")
        print(" Kaydet -> Render'da Manual Deploy yap.\n")
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

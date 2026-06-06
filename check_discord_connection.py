"""Discord API baglantisini test eder."""

import sys

import requests

URL = "https://discord.com/api/v10/gateway"


def main() -> None:
    print("Discord baglantisi test ediliyor...")
    print(f"Hedef: {URL}\n")
    try:
        r = requests.get(URL, timeout=15)
        print(f"[OK] Baglanti basarili — HTTP {r.status_code}")
        print("Bot calistirabilirsin: python run_firstmyko_bot.py")
    except requests.exceptions.ConnectionError:
        print("[HATA] discord.com'a baglanilamiyor!")
        print()
        print("Bu bot kodu hatasi DEGIL — ag/guvenlik duvari sorunu.")
        print()
        print("Cozum onerileri:")
        print("  1. Windows Guvenlik Duvari - python.exe icin izin ver")
        print("  2. Antivirus HTTPS taramasini KAPAT (Avast/Kaspersky)")
        print("  3. VPN acik/kapali dene")
        print("  4. DNS: 8.8.8.8 veya 1.1.1.1")
        print("  5. Tarayicida ac: https://discord.com/api/v10/gateway")
        print("  6. Botu VPS/sunucuda calistir (en garanti cozum)")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[HATA] Zaman asimi — internet yavas veya Discord erisilemiyor.")
        sys.exit(1)


if __name__ == "__main__":
    main()

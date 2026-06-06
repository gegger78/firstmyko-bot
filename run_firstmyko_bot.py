#!/usr/bin/env python3
"""FIRSTMYKO Discord Bot baslatici."""

import sys
import traceback

try:
    from firstmyko_bot.bot_main import main
except Exception:
    print("[HATA] Modul yuklenemedi:")
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    main()

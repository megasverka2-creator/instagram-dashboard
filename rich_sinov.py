#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sendRichMessage razvedkasi: bir nechta payload variantini sinab,
qaysi tuzilma ishlashini aniqlaydi. Natija: chat 775946529 + log."""
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT = "775946529"

MD = """# 🏆 Ofitsiant reytingi (SINOV)

**Davr:** 15–21 iyul

| № | Ofitsiant | Buyurtma | Savdo |
|---|-----------|----------|-------|
| 🥇 | Наймжон | 177 | 35.4 mln |
| 🥈 | Abdumurodov | 121 | 35.0 mln |
| 🥉 | Dior | 114 | 29.0 mln |

Bu rich message sinovi — jadval ko'rinsa, ishladi!"""


def urinish(nom, payload):
    print(f"\n=== {nom} ===", flush=True)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendRichMessage",
        data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            javob = json.loads(r.read().decode())
        print(f"OK: {json.dumps(javob, ensure_ascii=False)[:400]}", flush=True)
        return javob.get("ok", False)
    except urllib.error.HTTPError as e:
        print(f"XATO {e.code}: {e.read().decode()[:400]}", flush=True)
        return False
    except Exception as e:
        print(f"XATO: {e}", flush=True)
        return False


def main():
    variantlar = [
        ("1: rich_message.markdown",
         {"chat_id": CHAT, "rich_message": {"markdown": MD}}),
        ("2: rich_message.text + parse_mode",
         {"chat_id": CHAT, "rich_message": {"text": MD, "parse_mode": "Markdown"}}),
        ("3: markdown togridan-togri",
         {"chat_id": CHAT, "markdown": MD}),
        ("4: rich_message.html",
         {"chat_id": CHAT, "rich_message": {"html":
          "<h1>🏆 Sinov</h1><p><b>Rich HTML</b> ishlayaptimi?</p>"}}),
    ]
    for nom, p in variantlar:
        if urinish(nom, p):
            print(f"\n>>> MUVAFFAQIYAT: {nom} <<<", flush=True)
            return
    print("\n>>> Hech biri ishlamadi — xato matnlaridan aniqlaymiz <<<", flush=True)


if __name__ == "__main__":
    main()

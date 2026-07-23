#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich xabar ichida RASM sinovi: raw.githubusercontent havolasi ishlaydimi?
Bir vaqtda hashtag himoyasi ham sinaladi."""
import glob
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT = "775946529"
REPO_RAW = "https://raw.githubusercontent.com/megasverka2-creator/instagram-dashboard/main/"


def tg(metod, payload):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{metod}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "description": str(e)}


def main():
    rasmlar = sorted(glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg"))
    if not rasmlar:
        print("XATO: repoda rasm fayli topilmadi (png/jpg)")
        return
    fayl = rasmlar[0]
    url = REPO_RAW + fayl
    print(f"Sinov rasmi: {fayl}\nHavola: {url}", flush=True)

    md = (f"# Sinov maqolasi\n\n"
          f"![]({url})\n\n"
          f"\\#benison \\#sinov\n\n"
          f"Bu **rich maqola** ichida rasm ko'rinsa — asosiy to'siq yechildi.\n\n"
          f"## Manzillar\n\n"
          f"- Zarafshon, Mega Center, 2-qavat\n"
          f"- Uchquduq, Smart City, 3-qavat\n\n"
          f"[Telegram](https://t.me/benison_uz)")

    javob = tg("sendRichMessage", {"chat_id": CHAT, "rich_message": {"markdown": md}})
    print(f"ok={javob.get('ok')}", flush=True)
    if not javob.get("ok"):
        print(f"XATO: {json.dumps(javob, ensure_ascii=False)[:400]}", flush=True)
    else:
        bloklar = javob.get("result", {}).get("rich_message", {}).get("blocks", [])
        turlar = [b.get("type") for b in bloklar]
        print(f"Bloklar: {turlar}", flush=True)


if __name__ == "__main__":
    main()

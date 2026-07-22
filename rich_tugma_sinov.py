#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich xabar + inline tugma + tahrirlash sinovi (shaxsiy chatda).
Savollar: sendRichMessage reply_markup qabul qiladimi?
editMessageText rich_message bilan xabarni yangilay oladimi?"""
import json
import os
import time
import urllib.error
import urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT = "775946529"


def tg(method, payload):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
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
    tugmalar = {"inline_keyboard": [[
        {"text": "1. Kulcha", "callback_data": "sinov|1"},
        {"text": "2. Lag'mon", "callback_data": "sinov|2"},
    ]]}

    print("=== 1: sendRichMessage + tugmalar ===", flush=True)
    r1 = tg("sendRichMessage", {
        "chat_id": CHAT,
        "rich_message": {"markdown":
            "# 🧪 Rich + tugma sinovi\n\n"
            "| Taom | Muddat |\n|---|---|\n| Kulcha | 2 soat |\n| Lag'mon | 1 soat |\n\n"
            "Tugmalar ostida ko'rinsa — 1-savol yechildi. "
            "**Tugmani bosmang** — bu faqat ko'rinish sinovi."},
        "reply_markup": tugmalar})
    print(json.dumps(r1, ensure_ascii=False)[:500], flush=True)
    if not r1.get("ok"):
        print(">>> Rich + tugma ISHLAMADI — sabab yuqorida <<<", flush=True)
        return
    msg_id = r1["result"]["message_id"]
    print(f">>> Rich + tugma yuborildi (msg {msg_id}) <<<", flush=True)

    time.sleep(3)
    print("\n=== 2: editMessageText + rich_message ===", flush=True)
    r2 = tg("editMessageText", {
        "chat_id": CHAT, "message_id": msg_id,
        "rich_message": {"markdown":
            "# 🧪 Rich + tugma sinovi (TAHRIRLANDI ✅)\n\n"
            "| Taom | Muddat | Sabab |\n|---|---|---|\n"
            "| Kulcha | 2 soat | ✅ mahsulot tugadi |\n| Lag'mon | 1 soat | — |\n\n"
            "Bu matn tahrirlangan bo'lsa — 2-savol ham yechildi."},
        "reply_markup": tugmalar})
    print(json.dumps(r2, ensure_ascii=False)[:500], flush=True)
    if r2.get("ok"):
        print(">>> Tahrirlash ISHLADI — ikkala savol yechildi <<<", flush=True)
    else:
        print(">>> Tahrirlash ishlamadi — sabab yuqorida <<<", flush=True)


if __name__ == "__main__":
    main()

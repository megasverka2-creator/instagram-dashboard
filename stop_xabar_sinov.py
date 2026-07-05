#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST XABAR SINOVI (namuna, bir martalik)

"kafe boshqaruv" guruhiga (STOP_CHAT_ID) kechki stop-list xulosasining
NAMUNA ko'rinishini yuboradi: filial bloki + taxminiy ta'sir + sabab tugmalari.

MUHIM: Bu NAMUNA (haqiqiy stop-list emas — u apiLogin bilan keyin ulanadi).
Tugmalar ko'rinadi, lekin bosilganda hozircha javob bermaydi — tinglovchi
(Railway worker) keyingi bosqichda quriladi.

Secrets: TELEGRAM_TOKEN, STOP_CHAT_ID  (STOP_CHAT_ID bo'lmasa TELEGRAM_CHAT_ID)
"""

import json
import os
import sys
import urllib.request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("STOP_CHAT_ID", "") or os.environ.get("TELEGRAM_CHAT_ID", "")


def tg(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8", errors="replace")[:300]}


def sabab_tugmalar(filial, taom):
    def cb(kod):
        return f"s|{filial}|{taom}|{kod}"[:64]
    return [
        [
            {"text": "📦 Mahsulot tugadi", "callback_data": cb("mahsulot")},
            {"text": "🚚 Yetkazish kechikdi", "callback_data": cb("yetkazish")},
        ],
        [
            {"text": "🔧 Uskuna nosozligi", "callback_data": cb("uskuna")},
            {"text": "✍️ Boshqa", "callback_data": cb("boshqa")},
        ],
    ]


def main():
    if not (TOKEN and CHAT_ID):
        print("XATO: TELEGRAM_TOKEN yoki STOP_CHAT_ID sekreti yo'q.")
        sys.exit(1)
    print(f"Guruh (chat_id): {CHAT_ID}")

    bosh = (
        "🧪 <b>STOP-LIST SINOVI — NAMUNA</b>\n"
        "Bu kelgusi kechki xulosaning ko'rinishi. Ma'lumotlar haqiqiy emas.\n"
        "Tugmalar hozircha javob bermaydi (tinglovchi keyingi bosqichda)."
    )
    r = tg("sendMessage", {"chat_id": CHAT_ID, "text": bosh, "parse_mode": "HTML"})
    print("Sarlavha:", "OK" if r.get("ok") else r)

    blok = (
        "🏢 <b>Benison-MegaCenter</b> — bugungi stop (namuna)\n\n"
        "🍽 <b>Lavash klassik</b>\n"
        "⏱ Stopda: <b>3 soat 15 daqiqa</b> (10:20–13:35)\n"
        "💸 Taxminiy ta'sir: <b>~700 000 so'm</b> potensial tushum "
        "<i>(o'rtacha soatlik savdo asosida, taxminiy)</i>\n\n"
        "👨‍🍳 Oshpaz: sababni tugma bilan belgilang 👇"
    )
    r = tg("sendMessage", {
        "chat_id": CHAT_ID,
        "text": blok,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": sabab_tugmalar("benison_mc", "lavash")},
    })
    print("Filial bloki:", "OK" if r.get("ok") else r)

    if r.get("ok"):
        print("\nSINOV MUVAFFAQIYATLI — 'kafe boshqaruv' guruhida 2 ta xabar ko'rinishi kerak.")
    else:
        print("\nXATO — bot guruhda a'zomi/admin bo'lsa va STOP_CHAT_ID to'g'ri bo'lsa qayta urining.")
        sys.exit(1)


if __name__ == "__main__":
    main()

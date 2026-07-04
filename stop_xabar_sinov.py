#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST XABAR SINOVI (namuna, bir martalik)

Hozirgi ulangan guruhga (TELEGRAM_CHAT_ID) kechki stop-list xulosasining
NAMUNA ko'rinishini yuboradi: filial bloki + taxminiy ta'sir + sabab tugmalari.

MUHIM: Bu NAMUNA ma'lumot (haqiqiy stop-list emas — u apiLogin kelgach ulanadi).
Tugmalar ko'rinadi, lekin bosilganda hozircha javob bermaydi — tinglovchi
(Railway worker) keyingi bosqichda quriladi.

Secrets: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID (mavjud)
"""

import json
import os
import sys
import urllib.request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def tg(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def sabab_tugmalar(filial, taom):
    """Bir taom uchun 4 ta sabab tugmasi (callback_data <64 bayt)."""
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
        print("XATO: TELEGRAM_TOKEN yoki TELEGRAM_CHAT_ID sekreti yo'q.")
        sys.exit(1)

    # 1) Sarlavha xabari
    bosh = (
        "🧪 <b>STOP-LIST SINOVI — NAMUNA</b>\n"
        "Bu kelgusi kechki xulosaning ko'rinishi. Ma'lumotlar haqiqiy emas.\n"
        "Tugmalar hozircha javob bermaydi (tinglovchi keyingi bosqichda)."
    )
    r = tg("sendMessage", {"chat_id": CHAT_ID, "text": bosh, "parse_mode": "HTML"})
    print("Sarlavha:", "OK" if r.get("ok") else r)

    # 2) Filial bloki — namunaviy bitta taom (haqiqiysida har taomga alohida)
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
        print("\nSINOV MUVAFFAQIYATLI — guruhda 2 ta xabar ko'rinishi kerak.")
    else:
        print("\nXATO — javobni tekshiring (bot guruhda a'zomi? chat_id to'g'rimi?).")
        sys.exit(1)


if __name__ == "__main__":
    main()

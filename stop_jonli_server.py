#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — JONLI STOP-LIST (iikoServer / RMS API, bir martalik)

Eski server API (nomingiz.iiko.it/resto, login/parol) orqali stop-listni oladi.
Diler endpointni yoqqach ishlaydi. Bir necha yo'lni sinab, ishlaganini topadi,
taom/filial nomlarini aniqlaydi va "kafe boshqaruv" guruhiga yuboradi.

Faqat O'QIYDI. Secrets: IIKO_SERVER, IIKO_LOGIN, IIKO_PASS, TELEGRAM_TOKEN, STOP_CHAT_ID
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
LOGIN = os.environ.get("IIKO_LOGIN", "")
PASSWORD = os.environ.get("IIKO_PASS", "")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("STOP_CHAT_ID", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
TASHKENT = timezone(timedelta(hours=5))


def http_get(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception:
            return e.code, ""
    except Exception as e:
        return -1, str(e)


def tg_send(text):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": True}).encode("utf-8"),
        method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8", errors="replace")[:300]}


def auth():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    st, tok = http_get(f"{SERVER}/resto/api/auth?" + urllib.parse.urlencode({"login": LOGIN, "pass": sha1}))
    tok = (tok or "").strip()
    if st != 200 or len(tok) < 8:
        print(f"AUTH XATO: {st} — {tok[:80]}")
        tg_send("⚠️ Stop-list: iiko auth xato.")
        sys.exit(1)
    print("[✓] Auth OK")
    return tok


def main():
    if not (SERVER and LOGIN and PASSWORD and TG_TOKEN and CHAT_ID):
        print("XATO: kerakli sekretlardan biri yo'q (IIKO_* / TELEGRAM_TOKEN / STOP_CHAT_ID).")
        sys.exit(1)

    token = auth()
    try:
        # Stop-list uchun nomzod yo'llar (diler qaysinisini yoqqanini topamiz)
        nomzodlar = [
            f"{SERVER}/resto/api/v2/stopLists?key={token}",
            f"{SERVER}/resto/api/v2/stopLists/all?key={token}",
            f"{SERVER}/resto/api/stopLists?key={token}",
            f"{SERVER}/resto/api/v2/entities/stopList?key={token}",
            f"{SERVER}/resto/api/v2/reserve/stopList?key={token}",
        ]
        topildi_url, topildi_body = None, None
        for url in nomzodlar:
            st, body = http_get(url)
            qisqa = " ".join((body or "").split())
            belgi = "✓" if (st == 200 and qisqa not in ("", "[]", "{}")) else "✗"
            print(f"[{belgi}] {st}  {url.split('?')[0].replace(SERVER,'')}")
            if belgi == "✓" and not topildi_url:
                topildi_url, topildi_body = url, body

        if not topildi_url:
            print("\nHech qaysi stop-list yo'li ma'lumot bermadi.")
            tg_send("⚠️ Stop-list endpoint topilmadi — diler yoqqan aniq manzilni so'rang.")
            sys.exit(1)

        print(f"\n[✓] ISHLAYDIGAN YO'L: {topildi_url.split('?')[0].replace(SERVER,'')}")
        print("\n--- XOM JAVOB (namuna, log uchun) ---")
        print((topildi_body or "")[:1200])
        print("--- ------------------------------ ---\n")

        # Guruhga tasdiq xabari (formatni real javobga keyin moslaymiz)
        hozir = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
        try:
            data = json.loads(topildi_body)
            if isinstance(data, list):
                soni = len(data)
            elif isinstance(data, dict):
                soni = len(data.get("stopListItems", data.get("items", data)))
            else:
                soni = "?"
        except Exception:
            soni = "?"

        tg_send(
            f"✅ <b>Stop-list ulanishi ishladi</b> — {hozir}\n\n"
            f"Server stop-listni bermoqda (ishlaydigan endpoint topildi).\n"
            f"Topilgan yozuvlar: <b>{soni}</b>\n\n"
            f"<i>Endi to'liq yig'uvchi shu formatga moslab quriladi.</i>"
        )
        print("=" * 60)
        print(f"XULOSA: STOP-LIST ISHLAYDI ✓ (yozuvlar: {soni}). Guruhga tasdiq yuborildi.")
        print("Log'dagi XOM JAVOBni menga ko'rsating — yig'uvchini shunga moslayman.")
        print("=" * 60)
    finally:
        http_get(f"{SERVER}/resto/api/logout?key={token}")


if __name__ == "__main__":
    main()

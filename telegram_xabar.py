#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse Telegram Xabarchi
=============================
Har kuni ertalab (Toshkent 08:30) ishlaydi:
  - Bugun rejada post bo'lsa — eslatma yuboradi
  - Dushanba bo'lsa — qo'shimcha haftalik xulosa (statistika + savdo + yangi reja)

GitHub Secrets: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SAVDO_PAROL
Sinov rejimi: python telegram_xabar.py sinov  (dushanba kabi, xabarni chiqaradi)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SAVDO_PAROL = os.environ.get("SAVDO_PAROL", "")

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://megasverka2-creator.github.io/instagram-dashboard"

KUNLAR = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
ACCOUNTS = {"benison_uz": "Benison", "dieto_uz": "Dieto", "eddo_uz": "Eddo"}

# Savdo brendlari (filiallar yig'indisi)
BRANDS = {
    "Benison": ["Benison-MegaCenter", "Benison-Oila", "Smart City"],
    "Eddo": ["Eddo"],
    "Mazzona": ["Mazzona"],
}

SINOV = len(sys.argv) > 1 and sys.argv[1] == "sinov"


def load_json(name):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_savdo():
    """Shifrlangan savdo faylini ochish."""
    if not SAVDO_PAROL:
        return None
    try:
        import shifr
        return shifr.load_encrypted(os.path.join(BASE, "savdo_data.enc.json"), SAVDO_PAROL)
    except Exception:
        return None


def fmt(n):
    return f"{round(n):,}".replace(",", " ")


def fmt_mln(n):
    if n >= 1e9:
        return f"{n/1e9:.2f} mlrd".replace(".", ",")
    return f"{n/1e6:.1f} mln".replace(".", ",")


# =============================================================
#  Xabar qismlari
# =============================================================
def bugungi_eslatma(reja):
    """Bugungi rejadagi postlar eslatmasi."""
    today = KUNLAR[datetime.now().weekday()] if not SINOV else "Juma"
    lines = []
    for acc, name in ACCOUNTS.items():
        v = (reja.get("accounts") or {}).get(acc) or {}
        for p in v.get("plan", []):
            if p.get("day") == today:
                lines.append(f"  🍽 <b>{name}</b> {p.get('time','')} — {p.get('type','')}: {p.get('theme','')}")
    if not lines:
        return None
    return (f"📣 <b>Bugun post kuni!</b> ({today})\n\n" + "\n".join(lines) +
            f"\n\n✍️ Tayyor caption'lar: {SITE}/kontent_reja.html")


def haftalik_xulosa():
    """Dushanba: statistika + savdo + reja xulosasi."""
    msg = ["📊 <b>RestoPulse — haftalik xulosa</b>\n"]

    # Instagram
    ig = load_json("instagram_data.json")
    if ig and len(ig):
        last = ig[-1]
        week_ago = ig[max(0, len(ig) - 8)]
        msg.append("📱 <b>Instagram:</b>")
        for acc, name in ACCOUNTS.items():
            a = (last.get("accounts") or {}).get(acc)
            if not a:
                continue
            old = (week_ago.get("accounts") or {}).get(acc) or {}
            df = (a.get("followers", 0) or 0) - (old.get("followers", 0) or 0)
            sign = f"+{df}" if df >= 0 else str(df)
            msg.append(f"  {name}: {fmt(a.get('followers',0))} foll. ({sign}), "
                       f"qamrov {fmt(a.get('reach_7d',0))}, ER {a.get('engagement_rate',0)}%")
        msg.append("")

    # Savdo
    savdo = load_savdo()
    if savdo:
        days = savdo[-7:]
        msg.append("💰 <b>Savdo (7 kun):</b>")
        for brand, deps in BRANDS.items():
            rev = sum(
                (day.get("departments", {}).get(d, {}) or {}).get("revenue", 0)
                for day in days for d in deps
            )
            if rev:
                msg.append(f"  {brand}: {fmt_mln(rev)} so'm")
        msg.append("")

    # Yangi reja
    reja = load_json("kontent_reja_ai.json")
    if reja:
        msg.append(f"🤖 <b>Yangi AI reja tayyor</b> ({reja.get('generated_at','')[:10]})")
        for acc, name in ACCOUNTS.items():
            v = (reja.get("accounts") or {}).get(acc) or {}
            n = len(v.get("plan", []))
            if n:
                msg.append(f"  {name}: {n} ta post rejalashtirilgan")
            if v.get("review"):
                msg.append(f"  ↳ <i>{v['review'][:150]}</i>")
        msg.append(f"\n📋 To'liq reja: {SITE}/kontent_reja.html")
        msg.append(f"📈 Dashboard: {SITE}/")

    return "\n".join(msg)


# =============================================================
#  Yuborish
# =============================================================
def send(text):
    if SINOV or not TOKEN or not CHAT_ID:
        print("--- XABAR (sinov rejimi) ---")
        print(text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
        print("--- TAMOM ---\n")
        return True
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ok = json.loads(resp.read().decode()).get("ok")
            print("  Yuborildi:", "OK" if ok else "XATO")
            return ok
    except Exception as e:
        print(f"  ! Telegram xato: {e}")
        return False


def main():
    print(f"\n=== Telegram xabarchi: {datetime.now():%Y-%m-%d %H:%M} ===")
    if not SINOV and (not TOKEN or not CHAT_ID):
        print("  XATO: TELEGRAM_TOKEN / TELEGRAM_CHAT_ID Secret'lari topilmadi")
        sys.exit(1)

    is_monday = datetime.now().weekday() == 0 or SINOV

    # 1) Dushanba — haftalik xulosa
    if is_monday:
        send(haftalik_xulosa())

    # 2) Har kuni — bugungi eslatma (reja bo'lsa)
    reja = load_json("kontent_reja_ai.json")
    if reja:
        x = bugungi_eslatma(reja)
        if x:
            send(x)
        else:
            print("  Bugun rejada post yo'q — eslatma yuborilmadi")
    print("=== Tugadi ===\n")


if __name__ == "__main__":
    main()

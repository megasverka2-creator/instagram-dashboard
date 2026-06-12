# -*- coding: utf-8 -*-
"""
RestoPulse — Telegram kanal/guruh statistika kollektori
========================================================
Har kuni kanal va guruhlardagi a'zolar sonini yig'adi.

MUHIM XAVFSIZLIK: bu skript hech qachon xabar YUBORMAYDI.
Faqat o'qish so'rovlari ishlatiladi: getUpdates, getChat, getChatMemberCount.
TELEGRAM_CHAT_ID (jamoa chati) ga umuman tegmaydi — u faqat
kanallar ro'yxatidan chiqarib tashlash uchun o'qiladi.

Rejimlar (REJIM env o'zgaruvchisi):
  yigish    — (standart) tg_kanallar.json dagi har chat uchun a'zolar sonini
              telegram_kanal_data.json ga yozadi
  aniqlash  — bot yaqinda qo'shilgan kanal/guruhlarni getUpdates orqali topib,
              tg_kanallar.json ga qo'shadi (jamoa chati avtomatik chiqariladi)

Secrets: TELEGRAM_TOKEN (bor), TELEGRAM_CHAT_ID (faqat istisno uchun)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TEAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")  # faqat istisno qilish uchun
REJIM = os.environ.get("REJIM", "yigish").strip().lower()

KANALLAR_FAYL = "tg_kanallar.json"
DATA_FAYL = "telegram_kanal_data.json"

# Toshkent vaqti (UTC+5)
TOSHKENT = timezone(timedelta(hours=5))
BUGUN = datetime.now(TOSHKENT).strftime("%Y-%m-%d")


def api(method, **params):
    """Telegram Bot API ga faqat O'QISH so'rovi. sendMessage bu yerda YO'Q."""
    assert method in ("getUpdates", "getChat", "getChatMemberCount"), \
        f"Ruxsat etilmagan metod: {method}"
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode() if params else None
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            res = json.loads(e.read().decode())
        except Exception:
            res = {"ok": False, "description": str(e)}
    return res


def oqi_json(fayl, standart):
    if os.path.exists(fayl):
        try:
            with open(fayl, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return standart


def yoz_json(fayl, data):
    with open(fayl, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
#  ANIQLASH — bot qo'shilgan kanallarni topish
# ============================================================
def aniqlash():
    print("== ANIQLASH rejimi: bot qo'shilgan kanal/guruhlar qidirilmoqda ==")
    res = api("getUpdates", limit=100, allowed_updates='["my_chat_member","message","channel_post"]')
    if not res.get("ok"):
        print("  XATO:", res.get("description"))
        sys.exit(1)

    topilgan = {}
    for upd in res.get("result", []):
        chat = None
        if "my_chat_member" in upd:
            chat = upd["my_chat_member"].get("chat")
        elif "channel_post" in upd:
            chat = upd["channel_post"].get("chat")
        elif "message" in upd:
            chat = upd["message"].get("chat")
        if not chat:
            continue
        cid = str(chat.get("id"))
        ctype = chat.get("type", "")
        if ctype not in ("channel", "supergroup", "group"):
            continue  # shaxsiy chatlar kerak emas
        if TEAM_CHAT_ID and cid == str(TEAM_CHAT_ID):
            continue  # JAMOA CHATI hech qachon ro'yxatga kirmaydi
        topilgan[cid] = {
            "id": cid,
            "nom": chat.get("title", "Nomsiz"),
            "turi": "kanal" if ctype == "channel" else "guruh",
            "username": chat.get("username", ""),
        }

    if not topilgan:
        print("  Hech narsa topilmadi. Eslatma: getUpdates faqat oxirgi 24 soat")
        print("  ichidagi voqealarni ko'radi. Botni kanaldan chiqarib, qayta")
        print("  qo'shing va shu rejimni darhol qayta ishga tushiring.")
        return

    mavjud = oqi_json(KANALLAR_FAYL, {"_izoh": "RestoPulse kuzatadigan Telegram kanal/guruhlar. Nomini tahrirlash mumkin, id ga tegmang. Keraksizini o'chirib tashlang.", "chatlar": []})
    bor_idlar = {c["id"] for c in mavjud["chatlar"]}
    yangi = 0
    for cid, c in topilgan.items():
        if cid not in bor_idlar:
            mavjud["chatlar"].append(c)
            yangi += 1
            print(f"  + Qo'shildi: {c['nom']} ({c['turi']})")
        else:
            print(f"  = Allaqachon bor: {c['nom']}")
    yoz_json(KANALLAR_FAYL, mavjud)
    print(f"\n  Jami {len(mavjud['chatlar'])} ta chat kuzatuvda ({yangi} ta yangi).")
    print(f"  Tekshirish: GitHub'da {KANALLAR_FAYL} faylini oching.")


# ============================================================
#  YIG'ISH — kunlik a'zolar soni
# ============================================================
def yigish():
    print("== YIG'ISH rejimi: a'zolar soni o'qilmoqda ==")
    cfg = oqi_json(KANALLAR_FAYL, None)
    if not cfg or not cfg.get("chatlar"):
        print(f"  {KANALLAR_FAYL} bo'sh. Avval 'aniqlash' rejimini ishga tushiring")
        print("  (Actions -> Telegram kanal statistika -> Run workflow -> rejim: aniqlash)")
        sys.exit(0)

    bugungi = {"date": BUGUN, "chats": {}}
    for c in cfg["chatlar"]:
        cid = c["id"]
        res = api("getChatMemberCount", chat_id=cid)
        if res.get("ok"):
            son = res["result"]
            bugungi["chats"][cid] = {
                "nom": c.get("nom", cid),
                "turi": c.get("turi", ""),
                "azolar": son,
            }
            print(f"  {c.get('nom', cid)} ({c.get('turi','')}): {son:,} a'zo")
        else:
            print(f"  XATO {c.get('nom', cid)}: {res.get('description')}")

    if not bugungi["chats"]:
        print("  Hech qaysi chatdan ma'lumot olinmadi.")
        sys.exit(1)

    data = oqi_json(DATA_FAYL, [])
    # Bugungi yozuv bor bo'lsa — yangilaymiz (qayta ishga tushirishda dublikat bo'lmasin)
    data = [d for d in data if d.get("date") != BUGUN]
    data.append(bugungi)
    data.sort(key=lambda d: d.get("date", ""))
    # Maksimum 400 kunlik tarix
    data = data[-400:]
    yoz_json(DATA_FAYL, data)
    print(f"\n  Saqlandi: {DATA_FAYL} ({len(data)} kunlik yozuv)")


if __name__ == "__main__":
    if not TOKEN:
        print("XATO: TELEGRAM_TOKEN topilmadi")
        sys.exit(1)
    if REJIM == "aniqlash":
        aniqlash()
    else:
        yigish()

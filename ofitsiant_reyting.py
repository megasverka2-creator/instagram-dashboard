#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ofitsiant reytingi — haftalik hisobot (iiko OLAP asosida).
O'tgan 7 kun: filial kesimida har ofitsiantning buyurtmalari soni,
savdosi, o'rtacha cheki va mehmonlar soni. Telegram'ga yuboriladi.
Razvedka bilan tasdiqlangan maydonlar: OrderWaiter.Name, Department,
UniqOrderId.OrdersCount, DishDiscountSumInt, GuestNum.
Sekretlar: IIKO_LOGIN, IIKO_PASS, IIKO_SERVER, TELEGRAM_TOKEN."""
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

SERVER = os.environ["IIKO_SERVER"].rstrip("/")
LOGIN = os.environ["IIKO_LOGIN"]
PASSWORD = os.environ["IIKO_PASS"]
TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ.get("REYTING_CHAT_ID", "775946529")
THREAD_ID = os.environ.get("REYTING_THREAD_ID", "").strip()
TOP_N = 10


def api_get(path, params=None):
    url = f"{SERVER}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
        return r.read().decode("utf-8")


def api_post_json(path, params, body):
    url = f"{SERVER}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def login():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    token = api_get("/resto/api/auth", {"login": LOGIN, "pass": sha1}).strip()
    if not token or len(token) < 8:
        raise RuntimeError("Auth muvaffaqiyatsiz")
    return token


def logout(token):
    try:
        api_get("/resto/api/logout", {"key": token})
    except Exception:
        pass


def olap_waiters(token, date_from, date_to):
    body = {
        "reportType": "SALES",
        "buildSummary": "false",
        "groupByRowFields": ["Department", "OrderWaiter.Name"],
        "aggregateFields": ["DishDiscountSumInt", "UniqOrderId.OrdersCount", "GuestNum"],
        "filters": {
            "OpenDate.Typed": {
                "filterType": "DateRange", "periodType": "CUSTOM",
                "from": date_from, "to": date_to,
            },
            "DeletedWithWriteoff": {"filterType": "IncludeValues", "values": ["NOT_DELETED"]},
            "OrderDeleted": {"filterType": "IncludeValues", "values": ["NOT_DELETED"]},
        },
    }
    return api_post_json("/resto/api/v2/reports/olap", {"key": token}, body)


def pul(n):
    return f"{int(round(n)):,}".replace(",", " ")


def hisobot_tuz(data, date_from, date_to):
    qatorlar = data.get("data", data) if isinstance(data, dict) else data
    filiallar = {}
    for q in qatorlar:
        dep = q.get("Department") or "?"
        ofitsiant = (q.get("OrderWaiter.Name") or "").strip()
        if not ofitsiant:
            continue
        savdo = float(q.get("DishDiscountSumInt") or 0)
        buyurtma = float(q.get("UniqOrderId.OrdersCount") or 0)
        mehmon = float(q.get("GuestNum") or 0)
        filiallar.setdefault(dep, []).append(
            {"nom": ofitsiant, "savdo": savdo, "buyurtma": buyurtma, "mehmon": mehmon})

    if not filiallar:
        return "🏆 Ofitsiant reytingi\n\nMa'lumot topilmadi (davr: " \
               f"{date_from} — {date_to})."

    matn = (f"🏆 OFITSIANT REYTINGI\n"
            f"📅 Davr: {date_from} — {date_to}\n"
            f"(saralash: savdo bo'yicha, top-{TOP_N})\n")
    for dep in sorted(filiallar):
        royxat = sorted(filiallar[dep], key=lambda x: -x["savdo"])[:TOP_N]
        matn += f"\n🏢 {dep}\n"
        for i, o in enumerate(royxat, 1):
            chek = o["savdo"] / o["buyurtma"] if o["buyurtma"] else 0
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            matn += (f"{medal} {o['nom']}: {int(o['buyurtma'])} buyurtma, "
                     f"{pul(o['savdo'])} so'm, o'rt. chek {pul(chek)}\n")
    matn += "\n💡 Keyingi bosqich: QR mijoz baholari qo'shilgach, reyting ⭐ bilan to'ladi."
    return matn


def telegram_yubor(matn):
    bolaklar = []
    while matn:
        if len(matn) <= 4000:
            bolaklar.append(matn)
            break
        kes = matn.rfind("\n", 0, 4000)
        if kes < 500:
            kes = 4000
        bolaklar.append(matn[:kes])
        matn = matn[kes:].lstrip("\n")
    for i, bolak in enumerate(bolaklar):
        if len(bolaklar) > 1:
            bolak += f"\n\n({i + 1}/{len(bolaklar)})"
        p = {"chat_id": CHAT_ID, "text": bolak}
        if THREAD_ID:
            p["message_thread_id"] = THREAD_ID
        data = urllib.parse.urlencode(p).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data=data)
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.loads(r.read().decode()).get("ok")
        print(f"Telegram {i + 1}/{len(bolaklar)}: {'ok' if ok else 'XATO'}", flush=True)


def main():
    toshkent = datetime.now(timezone.utc) + timedelta(hours=5)
    kecha = (toshkent - timedelta(days=1)).date()
    boshi = kecha - timedelta(days=6)
    date_from, date_to = boshi.isoformat(), kecha.isoformat()
    print(f"Davr: {date_from} — {date_to}", flush=True)
    token = login()
    try:
        data = olap_waiters(token, date_from, date_to)
    finally:
        logout(token)
    matn = hisobot_tuz(data, date_from, date_to)
    print(matn, flush=True)
    telegram_yubor(matn)


if __name__ == "__main__":
    main()

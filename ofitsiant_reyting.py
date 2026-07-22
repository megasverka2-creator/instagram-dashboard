#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ofitsiant reytingi (iiko OLAP). Ikki rejim:
  filial  — har filial kartasi: taqsimot + kassa + top-10
  umumiy  — tarmoq bo'ylab yagona top-10 + jami
Ishga tushirish: python3 ofitsiant_reyting.py [filial|umumiy|hammasi]
Sekretlar: IIKO_LOGIN, IIKO_PASS, IIKO_SERVER, TELEGRAM_TOKEN.
Muhit: KASSIR_NOMLAR (vergul bilan), REYTING_CHAT_ID, REYTING_THREAD_ID."""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

SERVER = os.environ["IIKO_SERVER"].rstrip("/")
LOGIN = os.environ["IIKO_LOGIN"]
PASSWORD = os.environ["IIKO_PASS"]
TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ.get("REYTING_CHAT_ID", "775946529")
THREAD_ID = os.environ.get("REYTING_THREAD_ID", "").strip()
ISTISNO = {n.strip().lower() for n in os.environ.get("KASSIR_NOMLAR", "").split(",") if n.strip()}
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


def olap(token, date_from, date_to, group_fields, agg_fields):
    body = {
        "reportType": "SALES",
        "buildSummary": "false",
        "groupByRowFields": group_fields,
        "aggregateFields": agg_fields,
        "filters": {
            "OpenDate.Typed": {
                "filterType": "DateRange", "periodType": "CUSTOM",
                "from": date_from, "to": date_to,
            },
            "DeletedWithWriteoff": {"filterType": "IncludeValues", "values": ["NOT_DELETED"]},
            "OrderDeleted": {"filterType": "IncludeValues", "values": ["NOT_DELETED"]},
        },
    }
    natija = api_post_json("/resto/api/v2/reports/olap", {"key": token}, body)
    return natija.get("data", natija) if isinstance(natija, dict) else natija


def tur_nomi(order_type):
    t = (order_type or "").lower()
    if any(w in t for w in ["самовывоз", "olib", "навынос", "pickup", "вынос", "take"]):
        return "🥡 Olib ketish"
    if any(w in t for w in ["достав", "deliver", "yetkaz", "dostavka", "kuryer"]):
        return "🛵 Dostavka"
    return "🍽 Zal"


def pul(n):
    n = int(round(n))
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} mln".replace(".0 ", " ")
    return f"{n:,}".replace(",", " ")


def malumot_yig(token, date_from, date_to):
    ofis = olap(token, date_from, date_to,
                ["Department", "OrderWaiter.Name"],
                ["DishDiscountSumInt", "UniqOrderId.OrdersCount"])
    turlar = olap(token, date_from, date_to,
                  ["Department", "OrderType"], ["DishDiscountSumInt"])

    filiallar, kassa, taqsimot = {}, {}, {}
    for q in ofis:
        dep = q.get("Department") or "?"
        nom = (q.get("OrderWaiter.Name") or "").strip()
        if not nom:
            continue
        savdo = float(q.get("DishDiscountSumInt") or 0)
        buyurtma = float(q.get("UniqOrderId.OrdersCount") or 0)
        if nom.lower() in ISTISNO:
            kassa[dep] = kassa.get(dep, 0) + savdo
            continue
        filiallar.setdefault(dep, []).append(
            {"nom": nom, "savdo": savdo, "buyurtma": buyurtma})
    for q in turlar:
        dep = q.get("Department") or "?"
        xom = q.get("OrderType") or ""
        print(f"OrderType: '{xom}' -> {tur_nomi(xom)}", flush=True)
        s = float(q.get("DishDiscountSumInt") or 0)
        taqsimot.setdefault(dep, {})
        tk = tur_nomi(xom)
        taqsimot[dep][tk] = taqsimot[dep].get(tk, 0) + s
    return filiallar, kassa, taqsimot


def qator(i, o, filial=None):
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
    chek = o["savdo"] / o["buyurtma"] if o["buyurtma"] else 0
    joy = f" ({filial})" if filial else ""
    return (f"{medal} {o['nom']}{joy} — {pul(o['savdo'])} so'm "
            f"({int(o['buyurtma'])} ta, chek {pul(chek)})\n")


def filial_hisobot(filiallar, kassa, taqsimot, date_from, date_to):
    matn = f"🏆 OFITSIANT REYTINGI — filiallar kesimida\n📅 {date_from} — {date_to}\n"
    for dep in sorted(set(list(filiallar) + list(kassa) + list(taqsimot))):
        t = taqsimot.get(dep, {})
        jami = sum(t.values())
        matn += f"\n━━━━━━━━━━━━━━\n🏢 {dep} — jami {pul(jami)} so'm\n"
        if t:
            qism = " • ".join(f"{k.split()[0]} {round(v * 100 / jami)}%"
                              for k, v in sorted(t.items(), key=lambda x: -x[1]))
            matn += f"   {qism}\n"
        if dep in kassa:
            matn += f"   🧾 Kassa orqali: {pul(kassa[dep])} so'm\n"
        royxat = sorted(filiallar.get(dep, []), key=lambda x: -x["savdo"])[:TOP_N]
        if royxat:
            for i, o in enumerate(royxat, 1):
                matn += "   " + qator(i, o)
        else:
            matn += "   (ofitsiant kesimi yo'q — savdo kassa orqali yuritiladi)\n"
    return matn


def umumiy_hisobot(filiallar, kassa, taqsimot, date_from, date_to):
    hamma = []
    for dep, royxat in filiallar.items():
        for o in royxat:
            hamma.append({**o, "filial": dep})
    hamma.sort(key=lambda x: -x["savdo"])
    tarmoq_jami = sum(sum(t.values()) for t in taqsimot.values())
    matn = (f"🌐 UMUMIY REYTING — butun tarmoq\n📅 {date_from} — {date_to}\n"
            f"💰 Tarmoq jami savdo: {pul(tarmoq_jami)} so'm\n\n"
            f"TOP-{TOP_N} ofitsiant (barcha filiallar):\n")
    for i, o in enumerate(hamma[:TOP_N], 1):
        matn += qator(i, o, o["filial"])
    if kassa:
        matn += f"\n🧾 Kassa savdolari jami: {pul(sum(kassa.values()))} so'm\n"
    return matn


def rich_yubor(markdown_matn, oddiy_matn):
    """Avval sendRichMessage (markdown), xato bo'lsa oddiy matnga tushadi."""
    payload = {"chat_id": CHAT_ID, "rich_message": {"markdown": markdown_matn}}
    if THREAD_ID:
        payload["message_thread_id"] = int(THREAD_ID)
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendRichMessage",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.loads(r.read().decode()).get("ok")
        if ok:
            print("Rich xabar yuborildi", flush=True)
            return
        print("Rich ok=false, oddiy matnga o'tildi", flush=True)
    except Exception as e:
        print(f"Rich xato ({e}), oddiy matnga o'tildi", flush=True)
    telegram_yubor(oddiy_matn)


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


def md_jadval(royxat, filial_korsat=False):
    sarlavha = "| № | Ofitsiant |" + (" Filial |" if filial_korsat else "") + " Buyurtma | Savdo | Chek |\n"
    sarlavha += "|---|---|" + ("---|" if filial_korsat else "") + "---|---|---|\n"
    qatorlar = ""
    for i, o in enumerate(royxat, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, str(i))
        chek = o["savdo"] / o["buyurtma"] if o["buyurtma"] else 0
        fil = f" {o.get('filial', '')} |" if filial_korsat else ""
        qatorlar += (f"| {medal} | {o['nom']} |{fil} {int(o['buyurtma'])} | "
                     f"{pul(o['savdo'])} | {pul(chek)} |\n")
    return sarlavha + qatorlar


def filial_rich(filiallar, kassa, taqsimot, date_from, date_to):
    md = f"# 🏆 Ofitsiant reytingi — filiallar\n\n**Davr:** {date_from} — {date_to}\n"
    for dep in sorted(set(list(filiallar) + list(kassa) + list(taqsimot))):
        t = taqsimot.get(dep, {})
        jami = sum(t.values())
        md += f"\n## 🏢 {dep} — {pul(jami)} so'm\n"
        if t:
            md += " • ".join(f"{k} {round(v * 100 / jami)}%"
                             for k, v in sorted(t.items(), key=lambda x: -x[1])) + "\n"
        if dep in kassa:
            md += f"\n🧾 Kassa orqali: **{pul(kassa[dep])} so'm**\n"
        royxat = sorted(filiallar.get(dep, []), key=lambda x: -x["savdo"])[:TOP_N]
        if royxat:
            md += "\n" + md_jadval(royxat)
        else:
            md += "\n_(ofitsiant kesimi yo'q — savdo kassa orqali yuritiladi)_\n"
    return md


def umumiy_rich(filiallar, kassa, taqsimot, date_from, date_to):
    hamma = []
    for dep, royxat in filiallar.items():
        for o in royxat:
            hamma.append({**o, "filial": dep})
    hamma.sort(key=lambda x: -x["savdo"])
    tarmoq_jami = sum(sum(t.values()) for t in taqsimot.values())
    md = (f"# 🌐 Umumiy reyting — butun tarmoq\n\n"
          f"**Davr:** {date_from} — {date_to}\n\n"
          f"**💰 Tarmoq jami savdo:** {pul(tarmoq_jami)} so'm\n\n"
          f"## TOP-{TOP_N} ofitsiant\n\n")
    md += md_jadval(hamma[:TOP_N], filial_korsat=True)
    if kassa:
        md += f"\n🧾 Kassa savdolari jami: **{pul(sum(kassa.values()))} so'm**\n"
    return md


def main():
    rejim = (sys.argv[1] if len(sys.argv) > 1 else "hammasi").lower()
    toshkent = datetime.now(timezone.utc) + timedelta(hours=5)
    kecha = (toshkent - timedelta(days=1)).date()
    boshi = kecha - timedelta(days=6)
    date_from, date_to = boshi.isoformat(), kecha.isoformat()
    print(f"Rejim: {rejim}, davr: {date_from} — {date_to}", flush=True)
    token = login()
    try:
        filiallar, kassa, taqsimot = malumot_yig(token, date_from, date_to)
    finally:
        logout(token)
    if rejim in ("filial", "hammasi"):
        rich_yubor(filial_rich(filiallar, kassa, taqsimot, date_from, date_to),
                   filial_hisobot(filiallar, kassa, taqsimot, date_from, date_to))
    if rejim in ("umumiy", "hammasi"):
        rich_yubor(umumiy_rich(filiallar, kassa, taqsimot, date_from, date_to),
                   umumiy_hisobot(filiallar, kassa, taqsimot, date_from, date_to))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iiko Savdo Kollektori
======================
iiko Server API'dan kunlik savdo ma'lumotlarini yig'adi:
  - savdo_data.json     — kunlik tushum, cheklar, o'rtacha chek (filial bo'yicha)
  - savdo_taomlar.json  — oxirgi 7 kun eng ko'p sotilgan taomlar (filial bo'yicha)

GitHub Secrets: IIKO_SERVER (https://nomingiz.iiko.it), IIKO_LOGIN, IIKO_PASS
Har kuni avtomatik ishlaydi (GitHub Actions).
"""

import json
import os
import sys
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

# ╔═══════════════════════════════════════════════════════════╗
# ║  FILIAL → AKKAUNT MOSLASHUVI                                ║
# ║  Birinchi muvaffaqiyatli ishga tushirishdan keyin Actions   ║
# ║  logida iiko'dagi haqiqiy filial nomlari ko'rinadi —        ║
# ║  o'shanda shu lug'atni to'ldiramiz. Bo'sh bo'lsa, filial    ║
# ║  nomlari iiko'dagidek saqlanadi (bu ham ishlayveradi).      ║
# ╚═══════════════════════════════════════════════════════════╝
MAPPING = {
    # "iiko'dagi filial nomi": "benison_uz",
    # "Masalan Benison Yunusobod": "benison_uz",
}

SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
LOGIN = os.environ.get("IIKO_LOGIN", "")
PASSWORD = os.environ.get("IIKO_PASS", "")
SAVDO_PAROL = os.environ.get("SAVDO_PAROL", "")  # shifrlash kaliti (sayt paroli)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, "savdo_data.json")          # eski (ochiq) — faqat o'tish davri uchun o'qiladi
DISHES_FILE = os.path.join(BASE, "savdo_taomlar.json")
DATA_ENC = os.path.join(BASE, "savdo_data.enc.json")        # yangi shifrlangan fayllar
DISHES_ENC = os.path.join(BASE, "savdo_taomlar.enc.json")
TYPES_ENC = os.path.join(BASE, "savdo_turlar.enc.json")

import shifr

DAYS_BACK = 7  # har safar oxirgi 7 kunni yangilab yig'amiz (kech kelgan cheklar uchun)


# =============================================================
#  iiko API
# =============================================================
def api_get(path, params=None):
    url = f"{SERVER}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def api_post_json(path, params, body):
    url = f"{SERVER}{path}?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def login():
    """Token olish. iiko parolni SHA1 ko'rinishida qabul qiladi."""
    sha1 = hashlib.sha1(PASSWORD.encode("utf-8")).hexdigest()
    token = api_get("/resto/api/auth", {"login": LOGIN, "pass": sha1}).strip()
    if not token or len(token) < 8:
        raise RuntimeError(f"Auth muvaffaqiyatsiz: '{token[:50]}'")
    return token


def logout(token):
    """Litsenziya o'rnini bo'shatish — MUHIM!"""
    try:
        api_get("/resto/api/logout", {"key": token})
    except Exception:
        pass


def olap_sales_daily(token, date_from, date_to):
    """Kunlik savdo: sana + filial bo'yicha tushum va cheklar soni."""
    body = {
        "reportType": "SALES",
        "buildSummary": "false",
        "groupByRowFields": ["OpenDate.Typed", "Department"],
        "aggregateFields": ["DishDiscountSumInt", "UniqOrderId.OrdersCount"],
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


def olap_sales_by_type(token, date_from, date_to):
    """Buyurtma turi bo'yicha kunlik savdo: dostavka / zal / olib ketish."""
    body = {
        "reportType": "SALES",
        "buildSummary": "false",
        "groupByRowFields": ["OpenDate.Typed", "Department", "OrderType"],
        "aggregateFields": ["DishDiscountSumInt", "UniqOrderId.OrdersCount"],
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


# Buyurtma turini 3 guruhga moslash (iiko nomlari har xil bo'lishi mumkin)
def order_kind(order_type):
    t = (order_type or "").lower()
    if any(w in t for w in ["достав", "deliver", "yetkaz", "dostavka", "курьер", "kuryer"]):
        return "dostavka"
    if any(w in t for w in ["себе", "self", "olib", "навынос", "pickup", "вынос", "take"]):
        return "olib_ketish"
    return "zal"


def olap_top_dishes(token, date_from, date_to):
    """Eng ko'p sotilgan taomlar (filial + guruh bo'yicha)."""
    body = {
        "reportType": "SALES",
        "buildSummary": "false",
        "groupByRowFields": ["Department", "DishGroup", "DishName"],
        "aggregateFields": ["DishDiscountSumInt", "DishAmountInt"],
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


def dept_key(name):
    """Filial nomini akkaunt kalitiga aylantirish (MAPPING bo'yicha)."""
    return MAPPING.get(name, name)


# =============================================================
#  Asosiy jarayon
# =============================================================
def main():
    print(f"\n=== iiko savdo yig'ish: {datetime.now():%Y-%m-%d %H:%M} ===")

    if not SERVER or not LOGIN or not PASSWORD:
        print("  XATO: IIKO_SERVER / IIKO_LOGIN / IIKO_PASS Secret'lari topilmadi")
        sys.exit(1)
    if not SAVDO_PAROL:
        print("  XATO: SAVDO_PAROL Secret'i topilmadi (shifrlash uchun sayt paroli kerak)")
        sys.exit(1)

    today = datetime.now().date()
    date_from = (today - timedelta(days=DAYS_BACK)).isoformat()
    date_to = today.isoformat()
    print(f"  Davr: {date_from} — {date_to}")
    print(f"  Server: {SERVER}")

    token = None
    try:
        token = login()
        print("  Auth: OK")

        # --- 1. Kunlik savdo ---
        sales = olap_sales_daily(token, date_from, date_to)
        rows = sales.get("data", [])
        print(f"  Kunlik savdo qatorlari: {len(rows)}")

        # Sana -> filial -> ko'rsatkichlar
        daily = {}
        dept_names = set()
        for r in rows:
            date = (r.get("OpenDate.Typed") or "")[:10]
            dept = r.get("Department") or "?"
            dept_names.add(dept)
            revenue = r.get("DishDiscountSumInt") or 0
            checks = r.get("UniqOrderId.OrdersCount") or 0
            if not date:
                continue
            daily.setdefault(date, {})
            k = dept_key(dept)
            d = daily[date].setdefault(k, {"revenue": 0, "checks": 0})
            d["revenue"] += revenue
            d["checks"] += checks

        # O'rtacha chek
        for date in daily:
            for k, d in daily[date].items():
                d["revenue"] = round(d["revenue"])
                d["avg_check"] = round(d["revenue"] / d["checks"]) if d["checks"] else 0

        print("  Topilgan filiallar (MAPPING uchun):")
        for n in sorted(dept_names):
            mapped = MAPPING.get(n, "(moslanmagan — o'z nomida saqlanadi)")
            print(f"    - \"{n}\" -> {mapped}")

        # Tarixga qo'shish: shu davr kunlarini yangilab yozamiz
        history = shifr.load_encrypted(DATA_ENC, SAVDO_PAROL) or []
        if not history and os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                print("  (eski ochiq fayldan tarix olindi — endi shifrlanadi)")
            except (json.JSONDecodeError, IOError):
                history = []
        refreshed = set(daily.keys())
        history = [h for h in history if h.get("date") not in refreshed]
        for date in sorted(daily.keys()):
            history.append({"date": date, "departments": daily[date]})
        history.sort(key=lambda h: h.get("date", ""))
        shifr.save_encrypted(DATA_ENC, history, SAVDO_PAROL)
        print(f"  Saqlandi (shifrlangan): {DATA_ENC} (jami kunlar: {len(history)})")

        # --- 2. Top taomlar (oxirgi 7 kun) ---
        dishes = olap_top_dishes(token, date_from, date_to)
        drows = dishes.get("data", [])
        by_dept = {}
        for r in drows:
            dept = dept_key(r.get("Department") or "?")
            by_dept.setdefault(dept, []).append({
                "dish": r.get("DishName") or "?",
                "group": r.get("DishGroup") or "",
                "sum": round(r.get("DishDiscountSumInt") or 0),
                "amount": round(r.get("DishAmountInt") or 0),
            })
        for dept in by_dept:
            by_dept[dept] = sorted(by_dept[dept], key=lambda x: x["sum"], reverse=True)

        # 💡 Reklama nomzodlari: narxi yuqori (mediana+), sotuvi kam (mediana-)
        opportunities = {}
        for dept, items in by_dept.items():
            real = [x for x in items if x["amount"] >= 3 and x["sum"] > 0]
            if len(real) >= 10:
                prices = sorted(x["sum"] / x["amount"] for x in real)
                amounts = sorted(x["amount"] for x in real)
                med_price = prices[len(prices) // 2]
                med_amount = amounts[len(amounts) // 2]
                opp = [x for x in real
                       if (x["sum"] / x["amount"]) >= med_price and x["amount"] <= med_amount]
                opp.sort(key=lambda x: x["sum"] / x["amount"], reverse=True)
                opportunities[dept] = [
                    {"dish": x["dish"], "group": x.get("group", ""),
                     "price": round(x["sum"] / x["amount"]),
                     "amount": x["amount"], "sum": x["sum"]}
                    for x in opp[:8]
                ]

        # 🏪 Filialga xos taomlar: faqat bitta filialda sotilgan (5+ dona)
        dish_depts = {}
        for dept, items in by_dept.items():
            for x in items:
                k = x["dish"]
                dish_depts.setdefault(k, {})[dept] = dish_depts.get(k, {}).get(dept, 0) + x["amount"]
        exclusives = {}
        for dish, depts_map in dish_depts.items():
            total = sum(depts_map.values())
            if len(depts_map) == 1 and total >= 5:
                dept = next(iter(depts_map))
                exclusives.setdefault(dept, []).append({"dish": dish, "amount": total})
        for dept in exclusives:
            exclusives[dept] = sorted(exclusives[dept], key=lambda x: x["amount"], reverse=True)[:15]

        for dept in by_dept:
            by_dept[dept] = by_dept[dept][:10]

        shifr.save_encrypted(DISHES_ENC, {
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period": f"{date_from} — {date_to}",
            "departments": by_dept,
            "opportunities": opportunities,
            "exclusives": exclusives,
        }, SAVDO_PAROL)
        print(f"  Saqlandi (shifrlangan): {DISHES_ENC} ({len(by_dept)} filial, "
              f"{sum(len(v) for v in opportunities.values())} ta reklama nomzodi, "
              f"{sum(len(v) for v in exclusives.values())} ta filialga xos taom)")

        # --- 3. Buyurtma turi bo'yicha savdo (dostavka / zal / olib ketish) ---
        try:
            tdata = olap_sales_by_type(token, date_from, date_to)
            trows = tdata.get("data", [])
            # sana -> filial -> kind -> {revenue, checks}
            tdaily = {}
            tturlar = set()
            for r in trows:
                date = (r.get("OpenDate.Typed") or "")[:10]
                if not date:
                    continue
                dept = dept_key(r.get("Department") or "?")
                kind = order_kind(r.get("OrderType"))
                tturlar.add(r.get("OrderType") or "?")
                rev = round(r.get("DishDiscountSumInt") or 0)
                chk = r.get("UniqOrderId.OrdersCount") or 0
                node = tdaily.setdefault(date, {}).setdefault(dept, {})
                k = node.setdefault(kind, {"revenue": 0, "checks": 0})
                k["revenue"] += rev
                k["checks"] += chk

            thist = shifr.load_encrypted(TYPES_ENC, SAVDO_PAROL) or []
            refreshed_t = set(tdaily.keys())
            thist = [h for h in thist if h.get("date") not in refreshed_t]
            for date in sorted(tdaily.keys()):
                thist.append({"date": date, "departments": tdaily[date]})
            thist.sort(key=lambda h: h.get("date", ""))
            shifr.save_encrypted(TYPES_ENC, thist, SAVDO_PAROL)
            print(f"  Saqlandi (shifrlangan): {TYPES_ENC} (buyurtma turlari)")
            print("  iiko'dagi buyurtma turlari (moslandi):")
            for t in sorted(tturlar):
                print(f"    - \"{t}\" -> {order_kind(t)}")
        except Exception as e:
            print(f"  ! Buyurtma turi yig'ishda xato (qolgan ma'lumot saqlandi): {e}")

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"  ! API xato ({e.code}): {body}")
        sys.exit(1)
    except Exception as e:
        print(f"  ! Xato: {e}")
        sys.exit(1)
    finally:
        if token:
            logout(token)
            print("  Logout: OK (litsenziya bo'shatildi)")

    print("=== Tugadi ===\n")


if __name__ == "__main__":
    main()

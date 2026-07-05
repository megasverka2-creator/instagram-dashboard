#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — JONLI STOP-LIST (iikoCloud, StopList apiLogin, bir martalik)

api-ru.iiko.services orqali: token -> tashkilotlar -> nomenklatura (nomlar)
-> stop_lists. Haqiqiy stop-listni "kafe boshqaruv" guruhiga yuboradi.
Faqat o'qiydi. Secrets: IIKO_CLOUD_APILOGIN, TELEGRAM_TOKEN, STOP_CHAT_ID
"""
import json, os, sys, urllib.error, urllib.request
from datetime import datetime, timezone, timedelta

IIKO = "https://api-ru.iiko.services"
APILOGIN = os.environ.get("IIKO_CLOUD_APILOGIN", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("STOP_CHAT_ID", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
TASHKENT = timezone(timedelta(hours=5))

def post(path, body, token=None, timeout=90):
    req = urllib.request.Request(IIKO + path, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode())
        except Exception: return e.code, {}
    except Exception as e:
        return -1, {"xato": str(e)}

def tg(text):
    req = urllib.request.Request(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": True}).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return {"ok": False, "error": e.read().decode()[:300]}

def muddat(dateAdd):
    if not dateAdd: return None
    for f in ("%Y-%m-%d %H:%M:%S.%f","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S.%f","%Y-%m-%dT%H:%M:%S"):
        try:
            t = datetime.strptime(dateAdd[:26], f).replace(tzinfo=timezone.utc)
            m = max(0, int((datetime.now(timezone.utc)-t).total_seconds()//60))
            s, d = divmod(m, 60); return f"{s} soat {d} daqiqa" if s else f"{d} daqiqa"
        except Exception: continue
    return None

def main():
    if not (APILOGIN and TG_TOKEN and CHAT_ID):
        print("XATO: IIKO_CLOUD_APILOGIN / TELEGRAM_TOKEN / STOP_CHAT_ID dan biri yo'q."); sys.exit(1)
    token = None
    urinishlar = [
        ("apiKey+clientSecret(bir xil)", {"apiKey": APILOGIN, "clientSecret": APILOGIN}),
        ("clientId=StopList+secret",     {"clientId": "StopList", "clientSecret": APILOGIN, "apiKey": APILOGIN}),
        ("apiKey+empty clientSecret",    {"apiKey": APILOGIN, "clientSecret": ""}),
    ]
    for nom, body in urinishlar:
        st, j = post("/api/v2/access_token", body)
        tok = j.get("token") or j.get("access_token") or j.get("accessToken")
        info = tok[:10]+"…" if tok else json.dumps(j, ensure_ascii=False)[:220]
        print(f"    [{st}] {nom}: {info}")
        if st == 200 and tok:
            token = tok; print(f"[✓] Token olindi ({nom})"); break
    if not token:
        print("\n[✗] v2 hech qaysi kombinatsiya ishlamadi — ikkinchi maxfiy qiymat (clientSecret) kerak.")
        tg("⚠️ Stop-list: v2 token — dilerdan clientSecret so'rash kerak."); sys.exit(1)

    st, j = post("/api/1/organizations", {"returnAdditionalInfo": True}, token)
    orgs = j.get("organizations", []) if st == 200 else []
    org_nom = {o["id"]: (o.get("name") or o["id"]) for o in orgs}
    print(f"[✓] Filiallar: {len(orgs)} — {', '.join(org_nom.values())}")
    if not orgs:
        print("Javob:", json.dumps(j, ensure_ascii=False)[:300]); tg("⚠️ Filiallar topilmadi."); sys.exit(1)
    org_ids = list(org_nom.keys())

    nom = {}
    for oid in org_ids:
        st, j = post("/api/1/nomenclature", {"organizationId": oid}, token)
        if st == 200:
            for p in j.get("products", []):
                if p.get("id"): nom[p["id"]] = p.get("name") or p["id"]
    print(f"[✓] Nomenklatura: {len(nom)} ta taom nomi")

    st, j = post("/api/1/stop_lists", {"organizationIds": org_ids}, token)
    print(f"[{'✓' if st==200 else '✗'}] stop_lists: {st}")
    if st != 200:
        print("Javob:", json.dumps(j, ensure_ascii=False)[:400]); tg(f"⚠️ Stop-list o'qilmadi ({st})."); sys.exit(1)
    print("\n--- XOM (namuna) ---"); print(json.dumps(j, ensure_ascii=False)[:900]); print("--- --- ---\n")

    hozir = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
    filial = {}; jami = 0
    for blok in j.get("terminalGroupStopLists", []):
        nomi = org_nom.get(blok.get("organizationId"), blok.get("organizationId"))
        bag = filial.setdefault(nomi, [])
        for tgb in blok.get("items", []):
            for it in tgb.get("items", []):
                bag.append((nom.get(it.get("productId"), f"(id {str(it.get('productId'))[:8]}…)"),
                            it.get("balance"), muddat(it.get("dateAdd")))); jami += 1

    if jami == 0:
        matn = (f"✅ <b>Stop-list holati</b> — {hozir}\n\nAyni damda hech qaysi filialda stop yo'q.\n\n"
                f"<i>(Tizim iiko'ni muvaffaqiyatli o'qidi — ulanish ishladi.)</i>")
    else:
        q = [f"🛑 <b>Stop-list — ayni damda</b> ({hozir})\n"]
        for nomi, items in filial.items():
            if not items: continue
            q.append(f"\n🏢 <b>{nomi}</b> — {len(items)} ta:")
            for taom, bal, mud in items[:15]:
                q.append(f"  • {taom}" + (f" — {mud}" if mud else ""))
            if len(items) > 15: q.append(f"  … va yana {len(items)-15} ta")
        matn = "\n".join(q)[:4000]
    r = tg(matn); print("Telegram:", "OK" if r.get("ok") else r)
    print("="*60); print(f"XULOSA: JONLI O'QISH ISHLADI ✓ — {jami} ta stopda. Guruhga yuborildi."); print("="*60)

if __name__ == "__main__":
    main()

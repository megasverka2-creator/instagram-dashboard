#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — JONLI STOP-LIST (iikoCloud, StopList apiLogin, bir martalik)

api-ru.iiko.services orqali: token -> tashkilotlar -> nomenklatura (nomlar)
-> stop_lists. Haqiqiy stop-listni "kafe boshqaruv" guruhiga yuboradi.
Faqat o'qiydi. Secrets: IIKO_CLOUD_APILOGIN, TELEGRAM_TOKEN, STOP_CHAT_ID
"""
import json, os, sys, hashlib, re, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

IIKO = "https://api-ru.iiko.services"
APILOGIN = os.environ.get("IIKO_CLOUD_APILOGIN", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("STOP_CHAT_ID", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
# Server API — taom nomlari uchun (hamma taom shu yerda)
SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
SRV_LOGIN = os.environ.get("IIKO_LOGIN", "")
SRV_PASS = os.environ.get("IIKO_PASS", "")
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

def server_nomlar():
    """Server API (login/parol) orqali barcha taom nomlarini oladi: {productId: nom}."""
    nomlar = {}
    if not (SERVER and SRV_LOGIN and SRV_PASS):
        print("    (server sekretlari yo'q — nomlar olinmadi)")
        return nomlar
    def sget(url, timeout=60):
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except Exception as e:
            return -1, str(e)
    sha1 = hashlib.sha1(SRV_PASS.encode()).hexdigest()
    st, tok = sget(f"{SERVER}/resto/api/auth?" + urllib.parse.urlencode({"login": SRV_LOGIN, "pass": sha1}))
    tok = (tok or "").strip()
    if st != 200 or len(tok) < 8:
        print(f"    (server auth xato: {st})"); return nomlar
    try:
        # 1) v2 JSON mahsulotlar ro'yxati
        st, body = sget(f"{SERVER}/resto/api/v2/entities/products/list?key={tok}&includeDeleted=true")
        if st == 200 and body.strip().startswith(("[", "{")):
            try:
                data = json.loads(body)
                arr = data if isinstance(data, list) else data.get("response", data.get("products", []))
                for p in arr:
                    if p.get("id"): nomlar[p["id"]] = p.get("name") or p["id"]
            except Exception:
                pass
        # 2) v1 XML (agar v2 bo'sh bo'lsa)
        if not nomlar:
            st, body = sget(f"{SERVER}/resto/api/products?key={tok}")
            if st == 200:
                for m in re.finditer(r"<id>([0-9a-fA-F-]{36})</id>\s*<[^>]*?name>([^<]+)<", body):
                    nomlar[m.group(1)] = m.group(2)
                if not nomlar:  # boshqa tartib
                    for blok in re.findall(r"<productDto>.*?</productDto>", body, re.S):
                        i = re.search(r"<id>([0-9a-fA-F-]{36})</id>", blok)
                        n = re.search(r"<name>([^<]+)</name>", blok)
                        if i and n: nomlar[i.group(1)] = n.group(1)
    finally:
        sget(f"{SERVER}/resto/api/logout?key={tok}")
    return nomlar

def main():
    if not (APILOGIN and TG_TOKEN and CHAT_ID):
        print("XATO: IIKO_CLOUD_APILOGIN / TELEGRAM_TOKEN / STOP_CHAT_ID dan biri yo'q."); sys.exit(1)
    st, j = post("/api/1/access_token", {"apiLogin": APILOGIN})
    token = j.get("token")
    if st != 200 or not token:
        print(f"[✗] Token XATO {st}: {json.dumps(j, ensure_ascii=False)[:280]}")
        tg("⚠️ Stop-list: iiko token olinmadi (apiLogin tekshiring)."); sys.exit(1)
    print("[✓] Token olindi")

    st, j = post("/api/1/organizations", {"returnAdditionalInfo": True}, token)
    orgs = j.get("organizations", []) if st == 200 else []
    org_nom = {o["id"]: (o.get("name") or o["id"]) for o in orgs}
    print(f"[✓] Filiallar: {len(orgs)} — {', '.join(org_nom.values())}")
    if not orgs:
        print("Javob:", json.dumps(j, ensure_ascii=False)[:300]); tg("⚠️ Filiallar topilmadi."); sys.exit(1)
    org_ids = list(org_nom.keys())

    print("[·] Server tomondan taom nomlari olinmoqda...")
    nom = server_nomlar()
    print(f"[✓] Server nomlari: {len(nom)} ta")
    # Cloud nomenklatura — zaxira (server topmaganlarini to'ldiradi)
    for oid in org_ids:
        st, j = post("/api/1/nomenclature", {"organizationId": oid}, token)
        if st == 200:
            for p in j.get("products", []):
                if p.get("id") and p["id"] not in nom:
                    nom[p["id"]] = p.get("name") or p["id"]
    print(f"[✓] Jami nom lug'ati: {len(nom)} ta")

    st, j = post("/api/1/stop_lists", {"organizationIds": org_ids}, token)
    print(f"[{'✓' if st==200 else '✗'}] stop_lists: {st}")
    if st != 200:
        print("Javob:", json.dumps(j, ensure_ascii=False)[:400]); tg(f"⚠️ Stop-list o'qilmadi ({st})."); sys.exit(1)
    print("\n--- XOM (namuna) ---"); print(json.dumps(j, ensure_ascii=False)[:900]); print("--- --- ---\n")

    hozir = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
    LIMIT_SOAT = 72  # oxirgi 3 kun
    def soat_ichida(dateAdd):
        if not dateAdd: return None
        for f in ("%Y-%m-%d %H:%M:%S.%f","%Y-%m-%d %H:%M:%S","%Y-%m-%dT%H:%M:%S.%f","%Y-%m-%dT%H:%M:%S"):
            try:
                t = datetime.strptime(dateAdd[:26], f).replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - t).total_seconds() / 3600
            except Exception: continue
        return None

    filial = {}       # nomi -> [(taom, mud_matn, soat)]  (faqat yangi, 3 kun ichida)
    eski_soni = {}    # nomi -> eski (3+ kun) stoplar soni
    jami = 0; jami_yangi = 0
    for blok in j.get("terminalGroupStopLists", []):
        nomi = org_nom.get(blok.get("organizationId"), blok.get("organizationId"))
        bag = filial.setdefault(nomi, [])
        for tgb in blok.get("items", []):
            for it in tgb.get("items", []):
                jami += 1
                soat = soat_ichida(it.get("dateAdd"))
                taom = nom.get(it.get("productId"), f"(id {str(it.get('productId'))[:8]}…)")
                if soat is not None and soat <= LIMIT_SOAT:
                    bag.append((taom, muddat(it.get("dateAdd")), soat)); jami_yangi += 1
                else:
                    eski_soni[nomi] = eski_soni.get(nomi, 0) + 1

    if jami == 0:
        matn = (f"✅ <b>Stop-list holati</b> — {hozir}\n\nAyni damda hech qaysi filialda stop yo'q.\n\n"
                f"<i>(Tizim iiko'ni muvaffaqiyatli o'qidi.)</i>")
    else:
        q = [f"🛑 <b>Stop-list — oxirgi 3 kun</b> ({hozir})\n"]
        for nomi, items in filial.items():
            eski = eski_soni.get(nomi, 0)
            items.sort(key=lambda x: x[2])  # eng yangisi oldin
            if not items and not eski:
                continue
            q.append(f"\n🏢 <b>{nomi}</b>")
            if items:
                for taom, mud, soat in items[:20]:
                    q.append(f"  • {taom}" + (f" — {mud}" if mud else ""))
            else:
                q.append("  <i>oxirgi 3 kunda yangi stop yo'q</i>")
            if eski:
                q.append(f"  <i>+ {eski} ta eski stop (3+ kun) — menyu tozalash kerak</i>")
        q.append(f"\n<i>Jami stopda: {jami} ta (yangi: {jami_yangi}, eski: {jami-jami_yangi})</i>")
        matn = "\n".join(q)[:4000]
    r = tg(matn); print("Telegram:", "OK" if r.get("ok") else r)
    print("="*60); print(f"XULOSA: {jami} ta stopda (yangi 3 kun: {jami_yangi}). Guruhga yuborildi."); print("="*60)

if __name__ == "__main__":
    main()

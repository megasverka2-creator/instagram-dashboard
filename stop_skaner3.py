#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST SKANER 3: 500 xatosining TO'LIQ MATNINI ko'rsatadi.
getDeliveryStopList uchun kerakli parametrni aniqlash. Faqat o'qiydi.
Secrets: IIKO_SERVER, IIKO_LOGIN, IIKO_PASS
"""
import hashlib, os, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta

SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
LOGIN = os.environ.get("IIKO_LOGIN", "")
PASSWORD = os.environ.get("IIKO_PASS", "")
EP = "/resto/api/v2/stopLists/getDeliveryStopList"

def http(url, timeout=40):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try: return e.code, e.read().decode("utf-8", errors="replace")
        except Exception: return e.code, ""
    except Exception as e:
        return -1, str(e)

def auth():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    st, tok = http(f"{SERVER}/resto/api/auth?" + urllib.parse.urlencode({"login": LOGIN, "pass": sha1}))
    tok = (tok or "").strip()
    if st != 200 or len(tok) < 8:
        print(f"AUTH XATO: {st}"); sys.exit(1)
    print("[✓] Auth OK"); return tok

def xato_matni(body):
    # HTML/JSON ichidan foydali xabarni ajratib olish
    b = body or ""
    m = re.search(r'"message"\s*:\s*"([^"]+)"', b) or re.search(r"<b>message</b>\s*([^<]+)<", b) \
        or re.search(r"<pre>([^<]+)</pre>", b) or re.search(r"(org[^<\"]{0,60}|date[^<\"]{0,60}|required[^<\"]{0,60}|null[^<\"]{0,60})", b, re.I)
    return (m.group(1).strip() if m else " ".join(b.split())[:400])

def main():
    if not (SERVER and LOGIN and PASSWORD):
        print("XATO: sekretlar yo'q."); sys.exit(1)
    token = auth()
    st, dep = http(f"{SERVER}/resto/api/corporation/departments?key={token}")
    ids = re.findall(r"<id>([0-9a-fA-F-]{36})</id>", dep or "")
    print(f"[✓] {len(ids)} filial id")
    oid = ids[0] if ids else ""
    bugun = datetime.now().strftime("%Y-%m-%d")
    kecha = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    sinovlar = [
        ("parametrsiz", f"{SERVER}{EP}?key={token}"),
        ("organization", f"{SERVER}{EP}?key={token}&organization={oid}"),
        ("departmentId", f"{SERVER}{EP}?key={token}&departmentId={oid}"),
        ("organization+dateFrom+dateTo", f"{SERVER}{EP}?key={token}&organization={oid}&dateFrom={kecha}&dateTo={bugun}"),
        ("department+date", f"{SERVER}{EP}?key={token}&department={oid}&date={bugun}"),
        ("organization+timestamp", f"{SERVER}{EP}?key={token}&organization={oid}&timestamp=0"),
    ]
    for nom, url in sinovlar:
        st, body = http(url)
        print(f"\n[{st}] {nom}")
        if st == 200:
            print("    ✓✓✓ ISHLADI! Namuna: " + " ".join((body or '').split())[:400])
        else:
            print("    Xato matni: " + xato_matni(body))
    print("\n" + "="*60)
    print("Yuqorida 200 chiqqan bo'lsa — o'sha usul. Bo'lmasa, 'Xato matni' larni menga bering.")
    print("="*60)

if __name__ == "__main__":
    main()

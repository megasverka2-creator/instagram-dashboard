#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST SKANER 2 (getDeliveryStopList, parametr bilan)

Oldingi skaner topdi: /resto/api/v2/stopLists/getDeliveryStopList 500 berdi
(manzil BOR, faqat organization/filial id kerak). Bu skript filiallarni olib,
o'sha endpointni turli parametr nomlari va usullar (GET/POST) bilan sinaydi.

Faqat o'qiydi. Secrets: IIKO_SERVER, IIKO_LOGIN, IIKO_PASS
"""

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
LOGIN = os.environ.get("IIKO_LOGIN", "")
PASSWORD = os.environ.get("IIKO_PASS", "")
EP = "/resto/api/v2/stopLists/getDeliveryStopList"


def http(url, method="GET", body=None, ctype=None, timeout=40):
    data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", errors="replace")
        except Exception:
            return e.code, ""
    except Exception as e:
        return -1, str(e)


def auth():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    st, tok = http(f"{SERVER}/resto/api/auth?" + urllib.parse.urlencode({"login": LOGIN, "pass": sha1}))
    tok = (tok or "").strip()
    if st != 200 or len(tok) < 8:
        print(f"AUTH XATO: {st}")
        sys.exit(1)
    print("[✓] Auth OK")
    return tok


def filial_idlar(token):
    st, body = http(f"{SERVER}/resto/api/corporation/departments?key={token}")
    ids = re.findall(r"<id>([0-9a-fA-F-]{36})</id>", body or "")
    # nomlar (id bilan yonma-yon)
    nomlar = re.findall(r"<name>([^<]+)</name>", body or "")
    print(f"[✓] Departments: {len(ids)} ta id topildi")
    return ids


def sinov(nom, st, body):
    ok = st == 200 and (body or "").strip() not in ("", "[]", "{}")
    belgi = "✓ 200 MA'LUMOT" if ok else (f"• 200 bo'sh" if st == 200 else f"✗ {st}")
    print(f"    [{belgi:16}] {nom}")
    if ok:
        print("        Namuna: " + " ".join((body or "").split())[:300])
    return ok


def main():
    if not (SERVER and LOGIN and PASSWORD):
        print("XATO: IIKO sekretlari yo'q.")
        sys.exit(1)
    token = auth()
    ids = filial_idlar(token)
    if not ids:
        print("Filial id topilmadi — departments javobi kutilganidan farqli.")
        # baribir parametrsiz bir marta sinaymiz
        ids = []

    topildi = []

    # 1) Parametrsiz (baza holat)
    print("\n--- Parametrsiz ---")
    st, body = http(f"{SERVER}{EP}?key={token}")
    if sinov("parametrsiz", st, body):
        topildi.append(("GET parametrsiz", f"{SERVER}{EP}?key={token}"))

    # 2) Har filial id bilan — turli parametr nomlari (GET)
    param_nomlari = ["organization", "organizationId", "departmentId", "department"]
    for oid in ids[:3]:  # dastlabki 3 filial yetarli
        print(f"\n--- Filial {oid[:8]}… (GET) ---")
        for p in param_nomlari:
            url = f"{SERVER}{EP}?key={token}&{p}={oid}"
            st, body = http(url)
            if sinov(f"GET {p}=…", st, body):
                topildi.append((f"GET {p}", url))
                break

    # 3) POST JSON (organizationIds massiv) — iikoCloud uslubi ba'zan serverda ham ishlaydi
    if ids:
        print(f"\n--- POST JSON (organizationIds) ---")
        payload = json.dumps({"organizationIds": ids[:3]})
        st, body = http(f"{SERVER}{EP}?key={token}", method="POST", body=payload,
                        ctype="application/json")
        if sinov("POST organizationIds[]", st, body):
            topildi.append(("POST organizationIds", f"{SERVER}{EP}"))

    print("\n" + "=" * 60)
    if topildi:
        print("✓✓✓ ISHLAYDIGAN USUL(LAR):")
        for nom, url in topildi:
            print(f"    {nom}")
        print("\nXULOSA: topildi — yig'uvchini shu usulga yozamiz.")
    else:
        print("XULOSA: hali parametr mos kelmadi. Yuqoridagi javob kodlarini menga ko'rsating —")
        print("500 matni ko'pincha kutilgan parametr nomini aytadi (masalan 'organization is required').")
    print("=" * 60)


if __name__ == "__main__":
    main()

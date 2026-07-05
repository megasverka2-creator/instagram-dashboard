#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST KENG SKANER (bir martalik, faqat o'qiydi)

iikoServer'ga auth qilib, o'nlab ehtimoliy stop-list manzilini ketma-ket
sinaydi (GET). Qaysi biri ma'lumot bersa — logda aniq ko'rsatadi.
Hech narsani o'zgartirmaydi.

Secrets: IIKO_SERVER, IIKO_LOGIN, IIKO_PASS
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SERVER = os.environ.get("IIKO_SERVER", "").rstrip("/")
LOGIN = os.environ.get("IIKO_LOGIN", "")
PASSWORD = os.environ.get("IIKO_PASS", "")


def http(url, method="GET", body=None, timeout=40):
    data = body.encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
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
        print(f"AUTH XATO: {st} — {tok[:80]}")
        sys.exit(1)
    print("[✓] Auth OK\n")
    return tok


def main():
    if not (SERVER and LOGIN and PASSWORD):
        print("XATO: IIKO_SERVER / IIKO_LOGIN / IIKO_PASS yo'q.")
        sys.exit(1)
    token = auth()

    # Ehtimoliy stop-list yo'llari (turli iikoServer versiyalarida)
    yollar = [
        "/resto/api/v2/stopLists",
        "/resto/api/v2/stopLists/all",
        "/resto/api/v2/stopLists/getDeliveryStopList",
        "/resto/api/v2/stopLists/getStopList",
        "/resto/api/stopLists",
        "/resto/api/stopList",
        "/resto/api/v2/entities/stopList",
        "/resto/api/v2/entities/list?rootType=StopListItem",
        "/resto/api/v2/reserve/stopList",
        "/resto/api/products/stopList",
        "/resto/api/nomenclature/stopList",
        "/resto/api/v2/stopList/items",
        "/resto/api/v2/stopLists/items",
        "/resto/api/v2/menu/stopList",
        "/resto/api/stoplist",
        "/resto/api/v2/stoplists",
    ]

    topildi = []
    for yol in yollar:
        # kalitni URL'ga qo'shamiz
        sep = "&" if "?" in yol else "?"
        url = f"{SERVER}{yol}{sep}key={token}"
        st, body = http(url)
        qisqa = " ".join((body or "").split())
        bor = st == 200 and qisqa not in ("", "[]", "{}") and "404" not in qisqa[:40]
        belgi = "✓ MA'LUMOT BOR" if bor else ("• bo'sh(200)" if st == 200 else f"✗ {st}")
        print(f"[{belgi:16}] {yol}")
        if bor:
            topildi.append((yol, body))

    print("\n" + "=" * 60)
    if topildi:
        for yol, body in topildi:
            print(f"\n✓✓✓ ISHLAYDI: {yol}")
            print("    Namuna javob:")
            print("    " + (body or "")[:900].replace("\n", "\n    "))
        print("\nXULOSA: yuqoridagi yo'l(lar) ishlaydi — yig'uvchini shunga yozamiz.")
    else:
        print("XULOSA: bu ro'yxatdagi hech biri ma'lumot bermadi.")
        print("Keyingi qadam: brauzerdan aniq URL'ni ushlash yoki dilerdan endpoint so'rash.")
    print("=" * 60)


if __name__ == "__main__":
    main()

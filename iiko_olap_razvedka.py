#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OLAP razvedka: SALES hisobotidagi BARCHA mavjud maydonlarni logga chiqaradi.
Maqsad: ofitsiant/stol/vaqt maydonlari qanday nomlanishini aniqlash.
Hech narsa yozmaydi, faqat o'qiydi. Sekretlar: IIKO_LOGIN, IIKO_PASS, IIKO_SERVER."""
import hashlib
import json
import os
import urllib.parse
import urllib.request

SERVER = os.environ["IIKO_SERVER"].rstrip("/")
LOGIN = os.environ["IIKO_LOGIN"]
PASS = os.environ["IIKO_PASS"]


def api_get(path, params=None):
    url = f"{SERVER}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
        return r.read().decode()


def main():
    sha1 = hashlib.sha1(PASS.encode()).hexdigest()
    token = api_get("/resto/api/auth", {"login": LOGIN, "pass": sha1}).strip()
    if not token or len(token) < 8:
        raise RuntimeError("Auth muvaffaqiyatsiz")
    try:
        xom = api_get("/resto/api/v2/reports/olap/columns",
                      {"key": token, "reportType": "SALES"})
        maydonlar = json.loads(xom)
        print(f"JAMI MAYDONLAR: {len(maydonlar)}\n")
        qiziq = ("waiter", "user", "table", "cashier", "employee",
                 "time", "guest", "order")
        print("=== QIZIQARLI MAYDONLAR (ofitsiant/stol/vaqt/mehmon) ===")
        for nom, info in sorted(maydonlar.items()):
            if any(k in nom.lower() for k in qiziq):
                print(f"  {nom}  |  {info.get('name', '')}  |  turi: {info.get('type', '?')}")
        print("\n=== TO'LIQ RO'YXAT ===")
        for nom, info in sorted(maydonlar.items()):
            print(f"  {nom}  |  {info.get('name', '')}")
    finally:
        try:
            api_get("/resto/api/logout", {"key": token})
        except Exception:
            pass


if __name__ == "__main__":
    main()

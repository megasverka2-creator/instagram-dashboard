#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RMS server API'da stop-list yo'lini qidiradi."""
import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request

SERVER = os.environ["IIKO_SERVER"].rstrip("/")
LOGIN = os.environ["IIKO_LOGIN"]
PASSWORD = os.environ["IIKO_PASS"]


def get(yol, params=None, timeout=40):
    url = f"{SERVER}{yol}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "replace")[:300]
        except Exception:
            return e.code, ""
    except Exception as e:
        return -1, str(e)[:200]


def main():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    st, tok = get("/resto/api/auth", {"login": LOGIN, "pass": sha1})
    tok = tok.strip()
    if st != 200 or len(tok) < 8:
        print(f"AUTH XATO: {st} {tok[:100]}")
        return
    print("Auth OK\n")
    yollar = [
        "/resto/api/v2/stopLists",
        "/resto/api/v2/stopList",
        "/resto/api/stopLists",
        "/resto/api/stopList",
        "/resto/api/v2/entities/stopList",
        "/resto/api/products/stopList",
        "/resto/api/v2/reports/stopList",
        "/resto/api/nomenclature/stopList",
        "/resto/api/v2/stopLists/getDeliveryStopList",
    ]
    try:
        for y in yollar:
            st, javob = get(y, {"key": tok})
            qisqa = javob[:150].replace("\n", " ")
            belgi = "OK" if st == 200 else "  "
            print(f"{belgi} {st}  {y}\n     {qisqa}\n")
    finally:
        get("/resto/api/logout", {"key": tok})


if __name__ == "__main__":
    main()

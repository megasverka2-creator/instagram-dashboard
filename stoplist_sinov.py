#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST SINOVI (bir martalik, faqat o'qiydi)

Maqsad: iikoServer (RMS) API'miz stop-list (to'xtatilgan taomlar) ma'lumotini
beradimi — aniqlash. Hech narsani o'zgartirmaydi, faqat GET so'rovlar.

Natija workflow logida ko'rinadi:
  - Har endpoint: HTTP holati + javob namunasi
  - Yakuniy xulosa: qaysi yo'l ishlaydi (yoki hech biri)

GitHub Secrets: IIKO_SERVER, IIKO_LOGIN, IIKO_PASS (savdo yig'uvchidagi bilan bir xil)
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


def http_get(url, timeout=45):
    """GET so'rov: (status, body[:800]) qaytaradi, xatoda ham natija beradi."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception as e:
        return -1, f"(ulanish xatosi: {e})"


def auth():
    sha1 = hashlib.sha1(PASSWORD.encode()).hexdigest()
    status, token = http_get(
        f"{SERVER}/resto/api/auth?" + urllib.parse.urlencode({"login": LOGIN, "pass": sha1})
    )
    token = (token or "").strip()
    if status != 200 or not token or len(token) < 8:
        print(f"AUTH XATO: status={status}, javob='{token[:80]}'")
        sys.exit(1)
    print(f"Auth OK (token uzunligi: {len(token)})")
    return token


def logout(token):
    http_get(f"{SERVER}/resto/api/logout?key={token}")


def sinov(nom, url):
    status, body = http_get(url)
    body_qisqa = " ".join((body or "").split())[:500]
    belgi = "✓" if status == 200 and body_qisqa else ("•" if status in (200, 204) else "✗")
    print(f"\n[{belgi}] {nom}")
    print(f"    URL: {url.split('?')[0]}")
    print(f"    Holat: {status}")
    print(f"    Javob: {body_qisqa[:400] or '(bo`sh)'}")
    return status, body


def main():
    if not (SERVER and LOGIN and PASSWORD):
        print("XATO: IIKO_SERVER / IIKO_LOGIN / IIKO_PASS sekretlari yo'q.")
        sys.exit(1)

    print(f"Server: {SERVER}")
    token = auth()
    ok_yollar = []

    try:
        # --- Nomzod endpointlar (turli iikoServer versiyalari turlicha ochadi) ---
        nomzodlar = [
            ("v2 stopLists",           f"{SERVER}/resto/api/v2/stopLists?key={token}"),
            ("v2 stopLists/all",       f"{SERVER}/resto/api/v2/stopLists/all?key={token}"),
            ("v1 stopLists",           f"{SERVER}/resto/api/stopLists?key={token}"),
            ("v2 entities stopList",   f"{SERVER}/resto/api/v2/entities/stopList?key={token}"),
        ]
        for nom, url in nomzodlar:
            status, body = sinov(nom, url)
            if status == 200 and (body or "").strip() not in ("", "[]", "{}"):
                ok_yollar.append(nom)

        # --- Foydali qo'shimcha: filiallar ro'yxati (chat_id/mapping uchun baribir kerak) ---
        sinov("Filiallar (departments)", f"{SERVER}/resto/api/corporation/departments?key={token}")

        # --- OLAP ustunlarida stop-listga oid maydon bormi? ---
        status, body = sinov(
            "OLAP ustunlari (SALES)",
            f"{SERVER}/resto/api/v2/reports/olap/columns?key={token}&reportType=SALES",
        )
        if status == 200 and body:
            past = body.lower()
            topilgan = [w for w in ("stop", "остановк", "запрет") if w in past]
            print(f"    Stop-ga oid maydonlar: {topilgan or 'topilmadi'}")

    finally:
        logout(token)

    print("\n" + "=" * 60)
    if ok_yollar:
        print(f"XULOSA: STOP-LIST BOR ✓ — ishlaydigan yo'l(lar): {', '.join(ok_yollar)}")
        print("Keyingi qadam: shu yo'l asosida 15-daqiqalik yig'uvchini quramiz.")
    else:
        print("XULOSA: to'g'ridan-to'g'ri stop-list endpointi topilmadi.")
        print("Variantlar: (1) yuqoridagi javoblarni menga ko'rsating — 404/403/formatga")
        print("qarab boshqa yo'l sinaymiz; (2) iikoCloud (apiLogin) orqali olish;")
        print("(3) iiko texnik yordamdan serverda stopList API yoqilganmi so'rash.")
    print("=" * 60)


if __name__ == "__main__":
    main()

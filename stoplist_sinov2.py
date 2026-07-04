#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — STOP-LIST SINOVI №2 (iikoCloud, bir martalik, faqat so'raydi)

Maqsad: iikoCloud API (apiLogin) orqali stop-list olinishini tekshirish.
Uch qadam: token olish -> tashkilotlar ro'yxati -> stop_lists so'rovi.
Hech narsani o'zgartirmaydi — faqat o'qish so'rovlari.

GitHub Secret: IIKO_CLOUD_APILOGIN  (iiko diler/texnik yordamdan olinadi)
"""

import json
import os
import sys
import urllib.error
import urllib.request

BAZA = "https://api-ru.iiko.services"
APILOGIN = os.environ.get("IIKO_CLOUD_APILOGIN", "").strip()


def post(path, body, token=None, timeout=45):
    url = BAZA + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body_txt = e.read().decode("utf-8", errors="replace")
        except Exception:
            body_txt = ""
        return e.code, {"xato": body_txt[:400]}
    except Exception as e:
        return -1, {"xato": f"ulanish: {e}"}


def main():
    if not APILOGIN:
        print("XATO: IIKO_CLOUD_APILOGIN sekreti yo'q.")
        print("GitHub -> Settings -> Secrets and variables -> Actions -> New secret")
        sys.exit(1)

    # 1) Token
    status, javob = post("/api/1/access_token", {"apiLogin": APILOGIN})
    if status != 200 or "token" not in javob:
        print(f"[✗] Token olinmadi. Holat: {status}")
        print(f"    Javob: {json.dumps(javob, ensure_ascii=False)[:400]}")
        print("\nEhtimoliy sabab: apiLogin noto'g'ri yoki hali faollashtirilmagan.")
        sys.exit(1)
    token = javob["token"]
    print(f"[✓] Token olindi (uzunligi: {len(token)})")

    # 2) Tashkilotlar
    status, javob = post("/api/1/organizations", {}, token)
    orglar = javob.get("organizations", []) if status == 200 else []
    print(f"\n[{'✓' if orglar else '✗'}] Tashkilotlar: holat={status}, topildi={len(orglar)} ta")
    for o in orglar[:10]:
        print(f"    - {o.get('name')}  (id: {o.get('id')})")
    if not orglar:
        print(f"    Javob: {json.dumps(javob, ensure_ascii=False)[:400]}")
        sys.exit(1)

    # 3) Stop-list
    org_ids = [o["id"] for o in orglar]
    status, javob = post("/api/1/stop_lists", {"organizationIds": org_ids}, token)
    print(f"\n[{'✓' if status == 200 else '✗'}] stop_lists: holat={status}")
    if status != 200:
        print(f"    Javob: {json.dumps(javob, ensure_ascii=False)[:500]}")
        sys.exit(1)

    jami = 0
    for blok in javob.get("terminalGroupStopLists", []):
        org_id = blok.get("organizationId", "?")
        org_nom = next((o.get("name") for o in orglar if o.get("id") == org_id), org_id)
        for tg in blok.get("items", []):
            elementlar = tg.get("items", [])
            jami += len(elementlar)
            print(f"    {org_nom} / terminal {str(tg.get('terminalGroupId'))[:8]}…: "
                  f"{len(elementlar)} ta pozitsiya stopda")
            for it in elementlar[:5]:
                print(f"        productId={str(it.get('productId'))[:13]}…  qoldiq={it.get('balance')}")

    print("\n" + "=" * 60)
    print(f"XULOSA: iikoCloud STOP-LIST ISHLAYDI ✓ — hozir jami {jami} ta pozitsiya stopda.")
    if jami == 0:
        print("(0 bo'lishi normal — ayni damda hech narsa stopda emas. Muhimi: so'rov 200 qaytardi.)")
    print("Keyingi qadam: 15-daqiqalik yig'uvchi (Railway worker) + taom nomlari lug'ati.")
    print("=" * 60)


if __name__ == "__main__":
    main()

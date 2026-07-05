#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — JONLI STOP-LIST TEKSHIRUVI (bir martalik)

iikoCloud'ga apiLogin bilan ulanib, AYNI DAMDAGI haqiqiy stop-listni o'qiydi,
taom va filial nomlarini aniqlaydi, va "kafe boshqaruv" guruhiga yuboradi.
Hozir hech narsa stopda bo'lmasa — buni ham yozadi (ishlayotganini tasdiqlaydi).

Faqat O'QIYDI (iiko tomonini o'zgartirmaydi). Telegramga faqat xabar yuboradi.

Secrets: IIKO_CLOUD_APILOGIN, TELEGRAM_TOKEN, STOP_CHAT_ID
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

IIKO = "https://api-ru.iiko.services"
APILOGIN = os.environ.get("IIKO_CLOUD_APILOGIN", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("STOP_CHAT_ID", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
TASHKENT = timezone(timedelta(hours=5))


def iiko_post(path, body, token=None, timeout=60):
    req = urllib.request.Request(IIKO + path, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}
    except Exception as e:
        return -1, {"xato": str(e)}


def tg_send(text):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
                         "disable_web_page_preview": True}).encode("utf-8"),
        method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8", errors="replace")[:300]}


def muddat(dateAdd):
    """dateAdd (iiko UTC) dan hozirgacha qancha o'tganini matn qiladi."""
    if not dateAdd:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            t = datetime.strptime(dateAdd[:26], fmt).replace(tzinfo=timezone.utc)
            mins = int((datetime.now(timezone.utc) - t).total_seconds() // 60)
            if mins < 0:
                mins = 0
            soat, daq = divmod(mins, 60)
            return f"{soat} soat {daq} daqiqa" if soat else f"{daq} daqiqa"
        except Exception:
            continue
    return None


def main():
    if not (APILOGIN and TG_TOKEN and CHAT_ID):
        print("XATO: IIKO_CLOUD_APILOGIN / TELEGRAM_TOKEN / STOP_CHAT_ID sekretlaridan biri yo'q.")
        sys.exit(1)

    # 1) Token
    st, j = iiko_post("/api/1/access_token", {"apiLogin": APILOGIN})
    if st != 200 or "token" not in j:
        print(f"[✗] Token XATO: {st} — {json.dumps(j, ensure_ascii=False)[:300]}")
        tg_send("⚠️ Stop-list tekshiruvi: iiko token olinmadi (apiLogin tekshiring).")
        sys.exit(1)
    token = j["token"]
    print(f"[✓] Token olindi")

    # 2) Tashkilotlar (filiallar)
    st, j = iiko_post("/api/1/organizations", {"returnAdditionalInfo": True}, token)
    orgs = j.get("organizations", []) if st == 200 else []
    org_nom = {o["id"]: (o.get("name") or o["id"]) for o in orgs}
    print(f"[✓] Filiallar: {len(orgs)} ta — {', '.join(org_nom.values())}")
    if not orgs:
        tg_send("⚠️ Stop-list tekshiruvi: filiallar topilmadi.")
        sys.exit(1)
    org_ids = list(org_nom.keys())

    # 3) Nomenklatura -> productId => nomi (har filial uchun)
    nom = {}
    for oid in org_ids:
        st, j = iiko_post("/api/1/nomenclature", {"organizationId": oid}, token, timeout=90)
        if st == 200:
            for p in j.get("products", []):
                if p.get("id"):
                    nom[p["id"]] = p.get("name") or p["id"]
    print(f"[✓] Nomenklatura: {len(nom)} ta taom nomi yuklandi")

    # 4) Stop-list
    st, j = iiko_post("/api/1/stop_lists", {"organizationIds": org_ids}, token)
    print(f"[{'✓' if st == 200 else '✗'}] stop_lists: holat={st}")
    if st != 200:
        print("    Javob:", json.dumps(j, ensure_ascii=False)[:400])
        tg_send(f"⚠️ Stop-list o'qilmadi (holat {st}).")
        sys.exit(1)

    # --- Diagnostika: xom tuzilma (birinchi qismi) ---
    print("\n--- XOM TUZILMA (namuna) ---")
    print(json.dumps(j, ensure_ascii=False)[:900])
    print("--- (log uchun) ---\n")

    # 5) Filial bo'yicha yig'ish
    hozir = datetime.now(TASHKENT).strftime("%Y-%m-%d %H:%M")
    filial_stop = {}   # org_nom -> [ (taom_nomi, balance, muddat_matn) ]
    jami = 0
    for blok in j.get("terminalGroupStopLists", []):
        oid = blok.get("organizationId")
        nomi = org_nom.get(oid, oid)
        bag = filial_stop.setdefault(nomi, [])
        for tg_blok in blok.get("items", []):
            for it in tg_blok.get("items", []):
                pid = it.get("productId")
                taom = nom.get(pid, f"(id {str(pid)[:8]}…)")
                bag.append((taom, it.get("balance"), muddat(it.get("dateAdd"))))
                jami += 1

    # 6) Xabar yasash
    if jami == 0:
        matn = (f"✅ <b>Stop-list holati</b> — {hozir}\n\n"
                f"Ayni damda hech qaysi filialda stop yo'q. Barcha taomlar mavjud.\n\n"
                f"<i>(Tizim iiko'ni muvaffaqiyatli o'qidi — tekshiruv ishladi.)</i>")
    else:
        qatorlar = [f"🛑 <b>Stop-list — ayni damda</b> ({hozir})\n"]
        for nomi, items in filial_stop.items():
            if not items:
                continue
            qatorlar.append(f"\n🏢 <b>{nomi}</b> — {len(items)} ta stopda:")
            for taom, bal, mud in items[:15]:
                q = f"  • {taom}"
                if mud:
                    q += f" — {mud}"
                qatorlar.append(q)
            if len(items) > 15:
                qatorlar.append(f"  … va yana {len(items) - 15} ta")
        matn = "\n".join(qatorlar)[:4000]

    r = tg_send(matn)
    print("Telegramga yuborildi:", "OK" if r.get("ok") else r)
    print("\n" + "=" * 60)
    print(f"XULOSA: jonli o'qish ISHLADI ✓ — hozir {jami} ta pozitsiya stopda. Guruhga yuborildi.")
    print("=" * 60)


if __name__ == "__main__":
    main()

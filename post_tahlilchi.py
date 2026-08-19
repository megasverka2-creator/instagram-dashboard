#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — AI Post-tahlilchi
================================
Har post chiqib, ko'rsatkichlari barqarorlashgach (>=2 kun), uni AI baholaydi:
  - baho (1-10) va daraja (Kuchli / O'rta / Zaif)
  - yutuq (nima yaxshi ishladi)
  - kamchilik (nimani yaxshilash kerak)
  - tavsiya (keyingi safar uchun aniq maslahat)

MUHIM: post AKKAUNTNING O'Z O'RTACHASIGA nisbatan baholanadi (adolatli).
Inkremental: har post faqat BIR MARTA baholanadi (id bo'yicha eslab qoladi).

Natija: post_tahlil.json
Manba:  instagram_data.json (instagram_collector.py yig'adi)
Secret: ANTHROPIC_API_KEY

Sinov rejimi (API chaqirmaydi, faqat nomzodlarni ko'rsatadi):
    python3 post_tahlilchi.py sinov
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# ── Sozlamalar ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"      # arzonroq kerak bo'lsa: "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
MATURITY_DAYS = 2                # post necha kun "yetilgandan" keyin baholanadi
MAX_NEW_PER_RUN = 6              # bir yurishda nechta yangi post (xarajatni cheklaydi)
CAPTION_LIMIT = 320             # AI'ga yuboriladigan caption uzunligi

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

BASE = os.path.dirname(os.path.abspath(__file__))
IG_ENC = os.path.join(BASE, "instagram_data.enc.json")
OUT_FILE = os.path.join(BASE, "post_tahlil.enc.json")   # endi SHIFRLANGAN saqlanadi
SAVDO_PAROL = os.environ.get("SAVDO_PAROL", "")          # shifrlash kaliti (sayt paroli)
import shifr

# Akkaunt nomlari (dashboard.js bilan bir xil)
ACC_NOM = {
    "benison_uz": "Benison",
    "dieto_uz": "Dieto",
    "eddo_uz": "Eddo",
}

KUNLAR = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


# ── Yordamchilar ────────────────────────────────────────────
def post_sana(ts):
    """'2026-06-02T15:29:28+0000' -> datetime."""
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")


def call_claude(prompt):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parts = [c.get("text", "") for c in data.get("content", []) if c.get("type") == "text"]
            return "".join(parts)
    except urllib.error.HTTPError as e:
        print(f"  ! API xato ({e.code}): {e.read().decode('utf-8', 'replace')[:200]}")
    except Exception as e:
        print(f"  ! Ulanish xatosi: {e}")
    return None


def parse_json(text):
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1:
        return None
    try:
        return json.loads(t[s:e + 1])
    except json.JSONDecodeError:
        return None


def baho_prompt(p, acc_nom, base):
    """Bitta post uchun AI so'rovi."""
    dt = post_sana(p["timestamp"])
    kun = KUNLAR[dt.weekday()]
    cap = (p.get("caption") or "").strip().replace("\n", " ")[:CAPTION_LIMIT]
    tip_avg = base["type_avg"].get(p["type"], base["avg_engagement"])

    return f"""Sen restoran SMM bo'yicha tajribali tahlilchisan. Quyidagi Instagram postni
SHU AKKAUNTNING O'Z O'RTACHASIGA nisbatan baholab ber. Boshqa akkaunt yoki "umumiy norma" bilan emas.

AKKAUNT: {acc_nom} (@{p.get('_acc','')})
Akkaunt o'rtacha qamrovi (reach): {base['avg_reach']}
Akkaunt o'rtacha faolligi (engagement): {base['avg_engagement']}
'{p['type']}' turidagi postlar o'rtacha faolligi: {tip_avg}

BAHOLANAYOTGAN POST:
Turi: {p['type']}
Chiqqan kuni: {kun}, soat {dt.strftime('%H:%M')}
Caption: "{cap}"
Qamrov (reach): {p.get('reach')}
Ko'rishlar (views): {p.get('views')}
Layklar: {p.get('likes')} | Izohlar: {p.get('comments')} | Saqlash: {p.get('saved')} | Ulashish: {p.get('shares')}
Umumiy engagement: {p.get('engagement')} | Post ER: {p.get('post_er')}%

Faqat shu JSON formatda javob qaytar (boshqa matn yozma):
{{
  "baho": <1 dan 10 gacha butun son>,
  "daraja": "Kuchli" yoki "O'rta" yoki "Zaif",
  "yutuq": "<1 jumla: nima yaxshi ishladi>",
  "kamchilik": "<1 jumla: nimani yaxshilash kerak>",
  "tavsiya": "<1 jumla: keyingi safar uchun aniq, amaliy maslahat>"
}}"""


# ── Asosiy oqim ─────────────────────────────────────────────
def main():
    sinov = len(sys.argv) > 1 and sys.argv[1] == "sinov"

    history = shifr.load_encrypted(IG_ENC, SAVDO_PAROL) if SAVDO_PAROL else None
    if not history:
        print("XATO: instagram ma'lumoti topilmadi/bo'sh.")
        # Bu haqiqiy xato — workflow qizil bo'lishi va xato_signal ogohlantirishi kerak.
        sys.exit(1)
    snap = history[-1]
    snap_date = datetime.strptime(snap["date"], "%Y-%m-%d").date()
    print(f"Oxirgi snapshot: {snap['date']}")

    # Avval baholangan postlar
    natijalar = []
    done_ids = set()
    prev = shifr.load_encrypted(OUT_FILE, SAVDO_PAROL) if SAVDO_PAROL else None
    if prev:
        natijalar = prev.get("postlar", [])
        done_ids = {x["id"] for x in natijalar}
    print(f"Avval baholangan: {len(done_ids)} ta")

    # Nomzodlarni yig'amiz
    nomzod = []
    for acc, a in snap.get("accounts", {}).items():
        avg_reach = a.get("avg_reach") or 1
        avg_eng = a.get("avg_engagement") or 1
        type_avg = {t: v.get("avg_engagement", avg_eng) for t, v in a.get("by_type", {}).items()}
        base = {"avg_reach": avg_reach, "avg_engagement": avg_eng, "type_avg": type_avg}
        for p in a.get("posts", []):
            if p["id"] in done_ids:
                continue
            try:
                age = (snap_date - post_sana(p["timestamp"]).date()).days
            except Exception:
                continue
            if age < MATURITY_DAYS:
                continue
            p = dict(p)
            p["_acc"] = acc
            p["_acc_nom"] = ACC_NOM.get(acc, acc)
            p["_base"] = base
            nomzod.append(p)

    # Eng yangilarini oldin
    nomzod.sort(key=lambda x: x["timestamp"], reverse=True)
    print(f"Yangi yetilgan nomzodlar: {len(nomzod)} ta")

    if sinov:
        for p in nomzod[:MAX_NEW_PER_RUN]:
            dt = post_sana(p["timestamp"])
            print(f"  • {p['_acc_nom']:8} {p['type']:14} {dt.strftime('%m-%d %H:%M')}  reach={p.get('reach')}  ER={p.get('post_er')}%")
        print("\n(SINOV rejimi — API chaqirilmadi, hech narsa saqlanmadi)")
        return

    if not nomzod:
        print("Yangi baholanadigan post yo'q.")
        # Ko'chish davri: shifrlangan fayl hali yo'q bo'lsa — mavjud natijani shifrlab saqlaymiz
        if SAVDO_PAROL and not os.path.exists(OUT_FILE) and natijalar:
            out = {
                "_izoh": "AI post-tahlilchi natijalari. Har post bir marta baholanadi. Avtomatik to'ldiriladi.",
                "yangilangan": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "postlar": natijalar,
            }
            shifr.save_encrypted(OUT_FILE, out, SAVDO_PAROL)
            print(f"  Ko'chirildi (shifrlangan): {len(natijalar)} ta mavjud natija.")
        print("Tugadi.")
        return

    if not API_KEY:
        print("XATO: ANTHROPIC_API_KEY topilmadi (GitHub Secret'ni tekshiring).")
        sys.exit(1)

    yangi = 0
    for p in nomzod[:MAX_NEW_PER_RUN]:
        dt = post_sana(p["timestamp"])
        print(f"  Baholanmoqda: {p['_acc_nom']} / {p['type']} / {dt.strftime('%Y-%m-%d')} ...")
        res = parse_json(call_claude(baho_prompt(p, p["_acc_nom"], p["_base"])))
        if not res:
            print("    ! baholanmadi (o'tkazib yuborildi)")
            continue
        natijalar.append({
            "id": p["id"],
            "akkaunt": p["_acc"],
            "akkaunt_nom": p["_acc_nom"],
            "type": p["type"],
            "sana": dt.strftime("%Y-%m-%d"),
            "vaqt": dt.strftime("%H:%M"),
            "kun": KUNLAR[dt.weekday()],
            "permalink": p.get("permalink", ""),
            "caption": (p.get("caption") or "")[:160],
            "reach": p.get("reach"),
            "engagement": p.get("engagement"),
            "post_er": p.get("post_er"),
            "baho": res.get("baho"),
            "daraja": res.get("daraja"),
            "yutuq": res.get("yutuq"),
            "kamchilik": res.get("kamchilik"),
            "tavsiya": res.get("tavsiya"),
            "tahlil_vaqti": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        yangi += 1

    natijalar.sort(key=lambda x: x["sana"], reverse=True)
    out = {
        "_izoh": "AI post-tahlilchi natijalari. Har post bir marta baholanadi. Avtomatik to'ldiriladi.",
        "yangilangan": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "postlar": natijalar,
    }
    if SAVDO_PAROL:
        shifr.save_encrypted(OUT_FILE, out, SAVDO_PAROL)
        print(f"\nTayyor: {yangi} ta yangi post baholandi. Jami: {len(natijalar)} ta. (shifrlangan)")
    else:
        print("\nOGOHLANTIRISH: SAVDO_PAROL yo'q — fayl saqlanmadi.")


if __name__ == "__main__":
    main()

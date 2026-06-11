#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Kontent Reja Generatori
===========================
instagram_data.json dagi haqiqiy ma'lumotni tahlil qilib, Claude AI orqali
haftalik kontent reja tuzadi va kontent_reja_ai.json ga saqlaydi.

Har dushanba GitHub Actions orqali avtomatik ishlaydi.
API kalit: ANTHROPIC_API_KEY (GitHub Secret'dan keladi).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# ╔═══════════════════════════════════════════════════════════╗
# ║  SOZLAMALAR — restoranlar haqida (tahrirlash mumkin)       ║
# ╚═══════════════════════════════════════════════════════════╝
RESTAURANTS = {
    "benison_uz": {
        "name": "Benison",
        "specialty": "milliy va zamonaviy taomlar, jonli muhit",
        "dishes": "osh, shashlik, lag'mon, somsa, sushi",
    },
    "dieto_uz": {
        "name": "Dieto",
        "specialty": "sog'lom va parhez taomlar, tezkor yetkazib berish",
        "dishes": "salatlar, smuzi, grill taomlar, parhez shirinliklar",
    },
    "eddo_uz": {
        "name": "Eddo",
        "specialty": "pitsa va fastfud, oilaviy muhit",
        "dishes": "pitsa, burger, lavash, kartoshka fri",
    },
}

POSTS_PER_WEEK = 4          # har restoran uchun haftasiga nechta post
MODEL = "claude-sonnet-4-6" # arzonroq kerak bo'lsa: "claude-haiku-4-5-20251001"

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, "instagram_data.json")
OUT_FILE = os.path.join(BASE, "kontent_reja_ai.json")


# =============================================================
#  Ma'lumotdan tahlil xulosasi tayyorlash (prompt uchun)
# =============================================================
def summarize(acc_key, acc):
    """Bitta akkaunt bo'yicha AI uchun qisqa, ammo boy xulosa."""
    r = RESTAURANTS.get(acc_key, {})
    lines = [
        f"### {r.get('name', acc_key)} (@{acc_key})",
        f"Yo'nalishi: {r.get('specialty', '-')}. Mashhur taomlari: {r.get('dishes', '-')}.",
        f"Followerlar: {acc.get('followers', 0)}, Engagement rate: {acc.get('engagement_rate', 0)}%, "
        f"Reach (7 kun): {acc.get('reach_7d', 0)}, Saqlashlar: {acc.get('total_saved', 0)}.",
    ]
    bt = acc.get("by_type", {})
    if bt:
        parts = [f"{t}: o'rtacha {v.get('avg_engagement', 0)} engagement ({v.get('count', 0)} post)"
                 for t, v in bt.items()]
        lines.append("Kontent turlari samarasi: " + "; ".join(parts) + ".")
    posts = acc.get("posts", [])[:6]
    if posts:
        lines.append("Eng yaxshi postlari (uslub namunalari):")
        for p in posts:
            ts = (p.get("timestamp") or "")[:16].replace("T", " soat ")
            cap = (p.get("caption") or "")[:110]
            lines.append(f"- [{p.get('type')}] eng={p.get('engagement')}, reach={p.get('reach')}, "
                         f"vaqt={ts}: \"{cap}\"")
    return "\n".join(lines)


def build_prompt(snapshot):
    """Claude uchun to'liq topshiriq matni."""
    sections = []
    for key in RESTAURANTS:
        acc = snapshot.get("accounts", {}).get(key)
        if acc:
            sections.append(summarize(key, acc))
    data_block = "\n\n".join(sections)

    return f"""Sen tajribali SMM-strateg va o'zbek tilida yozadigan kopirayter san. Quyida uchta restoranning HAQIQIY Instagram statistikasi va eng yaxshi postlari berilgan. Har bir restoranning o'z ovozi (uslubi) eng yaxshi postlarining caption'larida ko'rinadi — shu uslubni saqla.

{data_block}

VAZIFA: Har bir restoran uchun keyingi haftaga {POSTS_PER_WEEK} ta postdan iborat kontent reja tuz.

QOIDALAR:
1. Ma'lumotga asoslan: qaysi kontent turi (VIDEO/IMAGE/CAROUSEL_ALBUM) shu restoranda yaxshi ishlayotgan bo'lsa, ko'proq o'shani taklif qil; eng yaxshi postlar qaysi soatda chiqqaniga qarab vaqt tanla.
2. Har restoranning mavjud uslubini davom ettir (masalan, hit bo'lgan seriyalar, hazil ohangi, emoji ishlatishi). Yaxshi ishlagan g'oyalarning davomini taklif qil.
3. Caption'lar O'ZBEK TILIDA, jonli, tayyor — to'g'ridan-to'g'ri Instagram'ga qo'yiladigan darajada. Har biri 2-4 qator + chaqiriq (CTA) + 4-5 ta hashtag.
4. Kunlarni hafta bo'ylab taqsimla (ketma-ket kunlarga to'plama).
5. Har postga qisqa "nima uchun" izohi yoz (data asosida).

JAVOBNI FAQAT QUYIDAGI JSON FORMATDA QAYTAR (boshqa hech qanday matn, izoh yoki ``` belgilarisiz):
{{
  "accounts": {{
    "benison_uz": {{
      "insight": "1-2 jumlalik asosiy xulosa: bu restoranда nima ishlayapti va rejada nimaga urg'u berildi",
      "plan": [
        {{"day": "Dushanba", "time": "12:30", "type": "VIDEO", "theme": "qisqa mavzu nomi", "why": "nima uchun aynan shu (data asosida, 1 jumla)", "caption": "to'liq tayyor caption matni hashtag'lar bilan"}}
      ]
    }},
    "dieto_uz": {{ ... xuddi shunday ... }},
    "eddo_uz": {{ ... xuddi shunday ... }}
  }}
}}

Kun nomlari faqat: Dushanba, Seshanba, Chorshanba, Payshanba, Juma, Shanba, Yakshanba.
Type faqat: VIDEO, IMAGE, CAROUSEL_ALBUM."""


# =============================================================
#  Claude API chaqiruvi
# =============================================================
def call_claude(prompt):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
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
        err = e.read().decode("utf-8", errors="replace")
        print(f"  ! API xato ({e.code}): {err[:300]}")
        return None
    except Exception as e:
        print(f"  ! Ulanish xatosi: {e}")
        return None


def parse_json_response(text):
    """AI javobidan JSON ni xavfsiz ajratib olish."""
    if not text:
        return None
    t = text.strip()
    # ``` qobiqlarini olib tashlash
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    # Birinchi { dan oxirgi } gacha
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(t[start:end + 1])
    except json.JSONDecodeError as e:
        print(f"  ! JSON parse xatosi: {e}")
        return None


# =============================================================
#  Asosiy jarayon
# =============================================================
def main():
    print(f"\n=== AI Kontent Reja: {datetime.now():%Y-%m-%d %H:%M} ===")

    if not API_KEY:
        print("  XATO: ANTHROPIC_API_KEY topilmadi (GitHub Secret'ni tekshiring)")
        sys.exit(1)

    if not os.path.exists(DATA_FILE):
        print("  XATO: instagram_data.json topilmadi — avval ma'lumot yig'ish kerak")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
    if not history:
        print("  XATO: ma'lumot bo'sh")
        sys.exit(1)

    snapshot = history[-1]
    print(f"  Ma'lumot sanasi: {snapshot.get('date')}")

    prompt = build_prompt(snapshot)
    print(f"  Claude'ga yuborilmoqda (model: {MODEL})...")
    answer = call_claude(prompt)
    plan = parse_json_response(answer)

    if not plan or "accounts" not in plan:
        print("  XATO: AI javobini o'qib bo'lmadi")
        if answer:
            print("  Javob boshi:", answer[:200])
        sys.exit(1)

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_date": snapshot.get("date"),
        "model": MODEL,
        "accounts": plan["accounts"],
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    for k, v in plan["accounts"].items():
        print(f"  -> {k}: {len(v.get('plan', []))} ta post")
    print(f"  Saqlandi: {OUT_FILE}")
    print("=== Tugadi ===\n")


if __name__ == "__main__":
    main()

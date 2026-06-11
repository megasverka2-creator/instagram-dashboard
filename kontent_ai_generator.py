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
MAX_TOKENS = 12000          # AI javobi uchun yetarli joy (3 restoran x 4 post + tahlillar)

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


def last_week_review(snapshot):
    """O'tgan hafta rejasi + haqiqatda chiqqan postlar — AI o'rganishi uchun."""
    sections = []

    # 1) O'tgan AI reja (bo'lsa)
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, "r", encoding="utf-8") as f:
                prev = json.load(f)
            lines = [f"O'TGAN HAFTA REJASI (sen tuzgansan, {prev.get('generated_at', '?')}):"]
            for key, v in prev.get("accounts", {}).items():
                items = [f"{p.get('day')} {p.get('time')} [{p.get('type')}] {p.get('theme')}"
                         for p in v.get("plan", [])]
                if items:
                    lines.append(f"- {key}: " + " | ".join(items))
            sections.append("\n".join(lines))
        except Exception:
            pass

    # 2) Oxirgi 7 kunda haqiqatda chiqqan postlar va natijalari
    from datetime import timedelta, timezone as tz
    week_ago = datetime.now(tz.utc) - timedelta(days=7)
    lines = ["OXIRGI 7 KUNDA HAQIQATDA CHIQQAN POSTLAR (natijalari bilan):"]
    found = False
    for key, acc in snapshot.get("accounts", {}).items():
        for p in acc.get("posts", []):
            ts = p.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+0000", "+00:00"))
                if dt >= week_ago:
                    cap = (p.get("caption") or "")[:70]
                    lines.append(f"- {key}: [{p.get('type')}] {ts[:16]} eng={p.get('engagement')}, "
                                 f"reach={p.get('reach')}: \"{cap}\"")
                    found = True
            except Exception:
                continue
    if found:
        sections.append("\n".join(lines))

    if not sections:
        return ""
    return ("\n\n" + "\n\n".join(sections) +
            "\n\nO'RGANISH: yuqoridagi reja va haqiqiy natijalarni solishtir. Qaysi tavsiyalar amalda bajarilgan va ishlagan? Qaysilari bajarilmagan yoki kutilgandek ishlamagan? Yangi rejani shu xulosalar asosida yaxshila. Har akkaunt uchun \"review\" maydonida o'tgan haftaga 1-2 jumlalik baho yoz (nima yaxshi ketdi, nimani o'zgartirdik).")


# Brend → iiko filiallari (savdo kontekstini bog'lash uchun)
IIKO_BRANDS = {
    "benison_uz": ["Benison-MegaCenter", "Benison-Oila", "Smart City"],
    "dieto_uz": [],  # Dieto savdosi Benison ichida — alohida ajratilmaydi
    "eddo_uz": ["Eddo"],
}


def sales_context():
    """iiko savdo ma'lumotlarini AI prompti uchun tayyorlash."""
    savdo_file = os.path.join(BASE, "savdo_data.json")
    taom_file = os.path.join(BASE, "savdo_taomlar.json")
    if not os.path.exists(savdo_file):
        return ""
    try:
        with open(savdo_file, "r", encoding="utf-8") as f:
            savdo = json.load(f)
        taomlar = None
        if os.path.exists(taom_file):
            with open(taom_file, "r", encoding="utf-8") as f:
                taomlar = json.load(f)
    except Exception:
        return ""
    if not savdo:
        return ""

    days = savdo[-7:]
    lines = ["SAVDO MA'LUMOTLARI (iiko, oxirgi 7 kun):"]
    for acc_key, deps in IIKO_BRANDS.items():
        if not deps:
            continue
        total_rev, total_checks = 0, 0
        day_revs = []
        for day in days:
            rev = sum((day.get("departments", {}).get(d, {}) or {}).get("revenue", 0) for d in deps)
            chk = sum((day.get("departments", {}).get(d, {}) or {}).get("checks", 0) for d in deps)
            total_rev += rev
            total_checks += chk
            day_revs.append((day.get("date", "?"), rev))
        avg = round(total_rev / total_checks) if total_checks else 0
        lines.append(f"\n{acc_key}: haftalik tushum {total_rev:,} so'm, {total_checks} chek, o'rtacha chek {avg:,} so'm")
        best = max(day_revs, key=lambda x: x[1]) if day_revs else None
        worst = min(day_revs, key=lambda x: x[1]) if day_revs else None
        if best and worst and best[1]:
            lines.append(f"  Eng kuchli kun: {best[0]} ({best[1]:,}), eng sust kun: {worst[0]} ({worst[1]:,})")
        # TOP taomlar (filiallar bo'yicha yig'ilgan)
        if taomlar and taomlar.get("departments"):
            agg = {}
            for d in deps:
                for x in taomlar["departments"].get(d, []):
                    k = x.get("dish", "?")
                    agg[k] = agg.get(k, 0) + (x.get("sum") or 0)
            top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:5]
            if top:
                lines.append("  TOP taomlar: " + "; ".join(f"{n} ({s:,})" for n, s in top))

        # 💡 Reklama nomzodlari: qimmat, lekin kam sotilayotgan taomlar
        if taomlar and taomlar.get("opportunities"):
            opp_agg = {}
            for d in deps:
                for x in taomlar["opportunities"].get(d, []):
                    k = x.get("dish", "?")
                    if k not in opp_agg or x.get("price", 0) > opp_agg[k]["price"]:
                        opp_agg[k] = {"price": x.get("price", 0), "amount": x.get("amount", 0)}
            opps = sorted(opp_agg.items(), key=lambda kv: kv[1]["price"], reverse=True)[:5]
            if opps:
                lines.append("  REKLAMA NOMZODLARI (narxi baland, lekin kam sotilyapti — mijozlar bilmaydi): "
                             + "; ".join(f"{n} (narxi {v['price']:,}, haftada bor-yo'g'i {v['amount']} dona)"
                                         for n, v in opps))

    lines.append("\nSAVDOdan FOYDALANISH: (1) Har brend rejasiga kamida 1 ta post REKLAMA NOMZODLARIdan biriga bag'ishlansin — bu qimmatli, lekin mijozlar bilmaydigan taom; uni 'yashirin xazina' / 'sinab ko'rganmisiz?' formatida jozibali tanishtir va why maydonida savdo sababini yoz. (2) TOP taomlarni ham ko'rsat — ular ishonchli traffik beradi. (3) Sust savdo kunlariga (yuqorida ko'rsatilgan) aksiya yoki jonli kontent rejalashtir. (4) O'rtacha chekni oshiradigan kombo/desert takliflarini caption'larga singdir. Dieto savdosi Benison oshxonasi ichida — Dieto uchun savdo raqamlariga emas, Instagram statistikasiga tayan.")
    return "\n\n" + "\n".join(lines)


def build_prompt(snapshot):
    """Claude uchun to'liq topshiriq matni."""
    sections = []
    for key in RESTAURANTS:
        acc = snapshot.get("accounts", {}).get(key)
        if acc:
            sections.append(summarize(key, acc))
    data_block = "\n\n".join(sections)
    review_block = last_week_review(snapshot)
    sales_block = sales_context()

    return f"""Sen tajribali SMM-strateg va o'zbek tilida yozadigan kopirayter san. Quyida uchta restoranning HAQIQIY Instagram statistikasi va eng yaxshi postlari berilgan. Har bir restoranning o'z ovozi (uslubi) eng yaxshi postlarining caption'larida ko'rinadi — shu uslubni saqla.

{data_block}{sales_block}{review_block}

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
      "review": "o'tgan hafta reja-natija solishtiruvi bo'yicha 1-2 jumlalik baho (ma'lumot bo'lmasa bo'sh qoldir)",
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
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            stop = data.get("stop_reason")
            if stop == "max_tokens":
                print("  ! OGOHLANTIRISH: javob token chegarasida kesildi (MAX_TOKENS'ni oshiring)")
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
            print("  Javob oxiri:", answer[-200:])
        sys.exit(1)

    # Eski rejani arxivga (oxirgi 8 hafta saqlanadi)
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            arxiv_file = os.path.join(BASE, "kontent_reja_arxiv.json")
            arxiv = []
            if os.path.exists(arxiv_file):
                with open(arxiv_file, "r", encoding="utf-8") as f:
                    arxiv = json.load(f)
            arxiv.append(old)
            arxiv = arxiv[-8:]
            with open(arxiv_file, "w", encoding="utf-8") as f:
                json.dump(arxiv, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

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

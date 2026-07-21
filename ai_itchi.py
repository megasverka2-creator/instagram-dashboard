#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse AI IT-chi (v1 — kuzatuvchi va tashxischi)
=====================================================
Har kuni ertalab ekotizim salomatligini tekshiradi:
  1. Barcha Actions workflow'larining oxirgi holati (GitHub API, GITHUB_TOKEN)
  2. Har bir .enc.json faylining "yoshi" (oxirgi commit sanasi)
  3. Faktlarni Claude'ga beradi → qisqa tashxis: ✅/⚠️/❌ + muammo bo'lsa
     sabab taxmini va Claude'ga tashlanadigan TAYYOR PROMPT
  4. Hisobotni Telegram'ga yuboradi

Sekretlar: ANTHROPIC_API_KEY, TELEGRAM_TOKEN (GitHub Secrets).
GITHUB_TOKEN — Actions o'zi beradi, sozlash kerak emas.
Sinov: python ai_itchi.py  (lokalda ham ishlaydi, tokenlar bo'lsa)
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "megasverka2-creator/instagram-dashboard")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("ITCHI_CHAT_ID", "775946529")  # standart: marketing xodimi
MODEL = "claude-sonnet-5"

# Fayl qanchalik tez yangilanishi kutiladi (kunda). Ro'yxatda yo'qlar tekshirilmaydi.
KUTILGAN_YOSH = {
    "savdo_data.enc.json": 2,
    "savdo_taomlar.enc.json": 2,
    "savdo_turlar.enc.json": 2,
    "savdo_taom_kun.enc.json": 2,
    "instagram_data.enc.json": 3,
    "telegram_kanal_data.enc.json": 3,
    "stop_tahlil.enc.json": 2,
    "izoh_tahlil.enc.json": 9,
    "post_tahlil.enc.json": 9,
}


def gh_api(yol):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "restopulse-itchi",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    req = urllib.request.Request(f"https://api.github.com{yol}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def yosh_kun(iso):
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds() / 86400
    except Exception:
        return None


def workflow_holati():
    """Har bir workflow'ning oxirgi run holati."""
    qatorlar = []
    try:
        wfs = gh_api(f"/repos/{REPO}/actions/workflows").get("workflows", [])
    except Exception as e:
        return [f"! Workflow ro'yxatini olib bo'lmadi: {e}"]
    for wf in wfs:
        if wf.get("state") != "active":
            continue
        try:
            runs = gh_api(
                f"/repos/{REPO}/actions/workflows/{wf['id']}/runs?per_page=1"
            ).get("workflow_runs", [])
        except Exception as e:
            qatorlar.append(f"{wf['name']}: holatini olib bo'lmadi ({e}) — bu XATO EMAS, tekshiruv muammosi")
            continue
        if not runs:
            qatorlar.append(f"{wf['name']}: hech qachon ishlamagan")
            continue
        r = runs[0]
        yosh = yosh_kun(r.get("updated_at", ""))
        yosh_s = f"{yosh:.1f} kun oldin" if yosh is not None else "?"
        qatorlar.append(
            f"{wf['name']}: {r.get('conclusion') or r.get('status')}, "
            f"{yosh_s} ({r.get('event')})"
        )
    return qatorlar


def fayl_yoshi():
    """Har bir kutilgan faylning oxirgi commit yoshi."""
    qatorlar = []
    for fayl, chegara in KUTILGAN_YOSH.items():
        try:
            c = gh_api(f"/repos/{REPO}/commits?path={fayl}&per_page=1")
            if not c:
                qatorlar.append(f"{fayl}: repo'da YO'Q (chegara {chegara} kun)")
                continue
            sana = c[0]["commit"]["committer"]["date"]
            yosh = yosh_kun(sana)
            belgi = "ESKIRGAN!" if (yosh is not None and yosh > chegara) else "ok"
            qatorlar.append(f"{fayl}: {yosh:.1f} kun oldin yangilangan, chegara {chegara} kun — {belgi}")
        except Exception as e:
            qatorlar.append(f"{fayl}: tekshirib bo'lmadi ({e})")
    return qatorlar


def claude_tashxis(faktlar):
    if not ANTHROPIC_KEY:
        return None
    system = (
        "Sen RestoPulse ekotizimining AI IT mutaxassisisan (\"AI IT-chi\"). "
        "Quyida GitHub Actions va ma'lumot fayllari bo'yicha XOM FAKTLAR berilgan. "
        "Ular asosida o'zbek tilida qisqa kunlik hisobot yoz.\n"
        "QOIDALAR:\n"
        "- Faqat faktlarga tayangan holda yoz, taxminlaringni 'ehtimol/taxminan' deb belgila, to'qima.\n"
        "- Tuzilma: avval bir qatorlik umumiy xulosa (hammasi yaxshi bo'lsa shu bilan deyarli tugat), "
        "keyin kerak bo'lsa ❌ Buzilgan, ⚠️ E'tibor kerak bo'limlari.\n"
        "- Har bir ❌ muammo uchun: 1-2 jumla sabab taxmini + «Claude'ga tayyor prompt:» deb, "
        "foydalanuvchi yangi Claude suhbatiga ko'chirib tashlashi mumkin bo'lgan aniq topshiriq matni.\n"
        "- Eslatma: 'Xato signali' workflow'i tez-tez neutral/skipped bo'ladi — bu normal, "
        "u faqat xato bo'lganda ishlaydi. Jadvali o'chirilgan workflow'lar cron-job.org orqali ishlaydi.\n"
        "- Umumiy hajm 900 belgidan oshmasin. Formatlash minimal: emoji + oddiy matn, Markdown ishlatma."
    )
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 700,
            "system": system,
            "messages": [{"role": "user", "content": faktlar}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode())
        return "".join(b.get("text", "") for b in data.get("content", [])).strip()
    except Exception as e:
        print(f"! Claude xatosi: {e}", flush=True)
        return None


def ai_yangiliklar():
    """AI olamidagi yangiliklar + RestoPulse uchun aniq takliflar (web search bilan)."""
    if not ANTHROPIC_KEY:
        return None
    system = (
        "Sen RestoPulse ekotizimining AI IT mutaxassisisan. RestoPulse — Navoiy viloyatidagi "
        "restoranlar tarmog'ining (Benison, Eddo, Mazzona) marketing avtomatikasi. Stack: "
        "Telegram botlar (python-telegram-bot, Railway), Claude API (tahlil, post matnlari, vision), "
        "OpenAI GPT Image (taom foto tahriri), Aisha AI STT (o'zbekcha ovoz), iiko (savdo/stop-list), "
        "GitHub Actions + Pages (yig'uvchilar, parolli sayt), Postgres. Egasi dasturchi emas — "
        "Claude tayyor fayl beradi, u push qiladi.\n"
        "VAZIFA: internetdan OXIRGI 2-3 haftadagi, aynan shu stack'ka tegishli AI yangiliklarini top "
        "va ulardan RestoPulse'ga amaliy foyda chiqar.\n"
        "QOIDALAR:\n"
        "- 2-4 ta eng muhim yangilik. Har biri: 1-2 jumla mohiyati + 'RestoPulse uchun:' aniq taklif.\n"
        "- Eng yaxshi 1 ta taklifga «Claude'ga tayyor prompt:» deb ko'chirib tashlanadigan topshiriq yoz.\n"
        "- Faqat topilgan faktlarga tayan, to'qima; ishonchsiz bo'lsa 'tekshirish kerak' de.\n"
        "- Umumiy reklama shovqinini emas, amaliy narsalarni tanla (API yangilanishi, narx o'zgarishi, "
        "yangi imkoniyat, muhim eskirish/deprecation).\n"
        "- O'zbek tilida, 1200 belgidan oshmasin, Markdown ishlatma, oddiy matn + emoji."
    )
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 1200,
            "system": system,
            "messages": [
                {
                    "role": "user",
                    "content": "Shu haftalik AI yangiliklari sharhini tayyorla. "
                    "Claude API, OpenAI image, o'zbekcha STT, Telegram bot ekotizimi, "
                    "restoran-marketing AI bo'yicha yangiliklarni qidir.",
                }
            ],
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
        return "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        ).strip()
    except Exception as e:
        print(f"! AI yangiliklar xatosi: {e}", flush=True)
        return None


def telegram_yubor(matn):
    """Uzun xabarni Telegram chegarasiga (4096) mos bo'laklarga bo'lib yuboradi."""
    bolaklar = []
    while matn:
        if len(matn) <= 4000:
            bolaklar.append(matn)
            break
        kes = matn.rfind("\n", 0, 4000)  # imkon qadar qator chegarasida kesamiz
        if kes < 500:
            kes = 4000
        bolaklar.append(matn[:kes])
        matn = matn[kes:].lstrip("\n")
    for i, bolak in enumerate(bolaklar):
        if len(bolaklar) > 1:
            bolak += f"\n\n({i + 1}/{len(bolaklar)})"
        data = urllib.parse.urlencode(
            {"chat_id": CHAT_ID, "text": bolak, "disable_web_page_preview": "true"}
        ).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data=data
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.loads(r.read().decode()).get("ok")
        print(f"Telegram bolak {i + 1}/{len(bolaklar)}: {'yuborildi' if ok else 'XATO'}", flush=True)


def main():
    import sys
    from datetime import timedelta

    wf = workflow_holati()
    fl = fayl_yoshi()
    faktlar = (
        f"Sana: {datetime.now(timezone.utc).isoformat()}\n\n"
        "=== WORKFLOW'LAR (oxirgi run) ===\n" + "\n".join(wf) +
        "\n\n=== MA'LUMOT FAYLLARI YOSHI ===\n" + "\n".join(fl)
    )
    print(faktlar, flush=True)

    hisobot = claude_tashxis(faktlar)
    if not hisobot:
        # AI ishlamasa ham xom faktlar boradi — hisobotsiz qolmaymiz
        hisobot = "🤖 AI IT-chi (AI tashxissiz, xom faktlar):\n\n" + faktlar
    else:
        hisobot = "🤖 AI IT-chi — kunlik tekshiruv\n\n" + hisobot

    telegram_yubor(hisobot)

    # Haftalik AI yangiliklari: dushanba (Toshkent) avtomatik yoki 'yangiliklar' argumenti bilan
    toshkent_kun = (datetime.now(timezone.utc) + timedelta(hours=5)).weekday()  # 0 = dushanba
    majburiy = len(sys.argv) > 1 and sys.argv[1] == "yangiliklar"
    if majburiy or toshkent_kun == 0:
        print("AI yangiliklari tayyorlanmoqda...", flush=True)
        yangilik = ai_yangiliklar()
        if yangilik:
            telegram_yubor("🧠 AI IT-chi — haftalik AI yangiliklari va takliflar\n\n" + yangilik)
        else:
            print("! Yangiliklar tayyorlanmadi (keyingi safar yana uriniladi)", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kommentariya-agenti ("Mijozlar ovozi")
=======================================
Har dushanba: Instagram izohlarini yig'adi -> AI tahlil qiladi ->
Telegram'ga hisobot yuboradi (kayfiyat, javobsiz savollar/lidlar,
tayyor javob qoralamalari) -> izoh_tahlil.json ga saqlaydi.

Secrets: IG_ACCESS_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

IG_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

SAVDO_PAROL = os.environ.get("SAVDO_PAROL", "")  # shifrlash kaliti (sayt paroli)
import shifr

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE, "izoh_tahlil.enc.json")  # endi SHIFRLANGAN saqlanadi
SITE = "https://megasverka2-creator.github.io/instagram-dashboard"

ACCOUNTS = {
    "benison_uz": {"id": "17841455964894264", "name": "Benison"},
    "dieto_uz": {"id": "17841479699303953", "name": "Dieto"},
    "eddo_uz": {"id": "17841461424798889", "name": "Eddo"},
}
DAYS_BACK = 14      # necha kunlik izohlar tahlil qilinadi
MODEL = "claude-sonnet-4-6"


# =============================================================
#  Instagram API
# =============================================================
def ig_get(path, params):
    params = dict(params, access_token=IG_TOKEN)
    url = f"https://graph.facebook.com/v21.0/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_comments(acc_key, acc):
    """Akkauntning oxirgi postlaridagi yangi izohlarni yig'ish."""
    since = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    media = ig_get(f"{acc['id']}/media", {
        "fields": "id,caption,timestamp,comments_count",
        "limit": 12,
    }).get("data", [])

    comments = []
    for m in media:
        if not m.get("comments_count"):
            continue
        try:
            data = ig_get(f"{m['id']}/comments", {
                "fields": "id,text,username,timestamp,like_count,replies{username}",
                "limit": 50,
            }).get("data", [])
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            raise PermissionError(err[:400])
        cap = (m.get("caption") or "")[:60]
        for c in data:
            ts = c.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("+0000", "+00:00"))
                if dt < since:
                    continue
            except Exception:
                pass
            uname = c.get("username", "")
            if uname == acc_key:
                continue  # o'zimizning izohlarimiz emas
            # Javob berilganmi: replies ichida akkauntning o'zi bormi
            replies = (c.get("replies") or {}).get("data", [])
            answered = any(r.get("username") == acc_key for r in replies)
            comments.append({
                "username": uname,
                "text": (c.get("text") or "")[:200],
                "sana": ts[:10],
                "likes": c.get("like_count", 0),
                "javob_berilgan": answered,
                "post": cap,
            })
    return comments


# =============================================================
#  AI tahlil
# =============================================================
def ai_analyze(all_comments):
    blocks = []
    for acc_key, items in all_comments.items():
        if not items:
            continue
        lines = [f"### {ACCOUNTS[acc_key]['name']} (@{acc_key}) — {len(items)} izoh:"]
        for c in items[:60]:
            tag = "JAVOBSIZ" if not c["javob_berilgan"] else "javob berilgan"
            lines.append(f"- @{c['username']} ({c['sana']}, {tag}): \"{c['text']}\" [post: {c['post']}]")
        blocks.append("\n".join(lines))
    if not blocks:
        return None

    prompt = f"""Sen restoran SMM-menejerisan. Quyida restoranlarning Instagram izohlari (oxirgi {DAYS_BACK} kun).

{chr(10).join(blocks)}

VAZIFA — har akkaunt bo'yicha:
1. Umumiy kayfiyatni baholash (ijobiy/salbiy/neytral foizlarda, taxminiy)
2. 2-3 jumlalik xulosa: mijozlar nimadan xursand, nimadan norozi, qanday mavzular ko'p
3. MUHIM: JAVOBSIZ qolgan savol/lid/shikoyatlarni ajrat (lid = sotib olish niyati: narx so'rash, manzil, yetkazib berish, bron). Har biriga qisqa, samimiy, o'zbekcha javob qoralamasini yoz (restoran nomidan, emoji bilan, narx aytmasdan — "Direct'ga yozdik" yoki telefon 55-510-80-08 ga yo'naltir).

FAQAT JSON qaytar:
{{"accounts": {{"benison_uz": {{"kayfiyat": {{"ijobiy": 80, "salbiy": 10, "neytral": 10}}, "xulosa": "...", "javobsiz": [{{"username": "...", "izoh": "...", "turi": "savol|lid|shikoyat", "javob": "tayyor javob matni"}}]}}, ...}}}}
Javobsiz ro'yxatiga eng muhim 5 tagachasini kirit."""

    body = json.dumps({
        "model": MODEL, "max_tokens": 6000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = "".join(c.get("text", "") for c in data.get("content", []) if c.get("type") == "text")
    s, e = text.find("{"), text.rfind("}")
    if s == -1:
        return None
    try:
        return json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return None


# =============================================================
#  Telegram hisobot
# =============================================================
def tg_send(text):
    if not TG_TOKEN or not TG_CHAT:
        print("--- TELEGRAM (token yo'q, namuna) ---\n" + text[:1500])
        return
    data = urllib.parse.urlencode({
        "chat_id": TG_CHAT, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("  Telegram:", "OK" if json.loads(resp.read().decode()).get("ok") else "XATO")
    except Exception as e:
        print(f"  ! Telegram xato: {e}")


def build_report(analysis, counts):
    msg = ["👂 <b>Mijozlar ovozi</b> (oxirgi 2 hafta)\n"]
    for acc_key, meta in ACCOUNTS.items():
        a = (analysis.get("accounts") or {}).get(acc_key)
        n = counts.get(acc_key, 0)
        if not a:
            if n == 0:
                msg.append(f"<b>{meta['name']}</b>: yangi izohlar yo'q")
            continue
        k = a.get("kayfiyat", {})
        msg.append(f"<b>{meta['name']}</b> — {n} izoh · 😊 {k.get('ijobiy', '?')}% / 😠 {k.get('salbiy', '?')}%")
        if a.get("xulosa"):
            msg.append(f"<i>{a['xulosa'][:250]}</i>")
        jb = a.get("javobsiz", [])
        if jb:
            msg.append(f"⚠️ <b>Javobsiz ({len(jb)}):</b>")
            for j in jb[:4]:
                turi = {"savol": "❓", "lid": "💰", "shikoyat": "🚨"}.get(j.get("turi"), "•")
                msg.append(f"{turi} @{j.get('username')}: \"{(j.get('izoh') or '')[:80]}\"")
                msg.append(f"   ↳ <i>Javob: {(j.get('javob') or '')[:150]}</i>")
        msg.append("")
    msg.append("💡 Javob qoralamalarini nusxalab, Instagram'da javob bering — har lid pul!")
    return "\n".join(msg)


# =============================================================
#  Asosiy
# =============================================================
def main():
    print(f"\n=== Mijozlar ovozi: {datetime.now():%Y-%m-%d %H:%M} ===")
    if not IG_TOKEN or not API_KEY:
        print("  XATO: IG_ACCESS_TOKEN yoki ANTHROPIC_API_KEY topilmadi")
        sys.exit(1)

    all_comments, counts = {}, {}
    for acc_key, acc in ACCOUNTS.items():
        try:
            items = collect_comments(acc_key, acc)
            all_comments[acc_key] = items
            counts[acc_key] = len(items)
            javobsiz = sum(1 for c in items if not c["javob_berilgan"])
            print(f"  {acc_key}: {len(items)} izoh ({javobsiz} ta javobsiz)")
        except PermissionError as e:
            print(f"  ! RUXSAT XATOSI ({acc_key}): {e}")
            print("  -> Token izohlarni o'qiy olmayapti. Tokenni 'instagram_manage_comments'")
            print("     ruxsati bilan qayta olish kerak (Graph API Explorer'da).")
            sys.exit(1)
        except Exception as e:
            print(f"  ! Xato ({acc_key}): {e}")
            all_comments[acc_key] = []
            counts[acc_key] = 0

    total = sum(counts.values())
    print(f"  Jami: {total} izoh")
    if total == 0:
        print("  Yangi izohlar yo'q — hisobot yuborilmaydi")
        return

    print("  AI tahlil qilmoqda...")
    analysis = ai_analyze(all_comments)
    if not analysis:
        print("  XATO: AI tahlilini o'qib bo'lmadi")
        sys.exit(1)

    data = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "counts": counts,
        "analysis": analysis,
    }
    if SAVDO_PAROL:
        shifr.save_encrypted(OUT_FILE, data, SAVDO_PAROL)
        print(f"  Saqlandi (shifrlangan): {OUT_FILE}")
    else:
        print("  OGOHLANTIRISH: SAVDO_PAROL yo'q — fayl saqlanmadi (Telegram baribir yuboriladi)")

    tg_send(build_report(analysis, counts))
    print("=== Tugadi ===\n")


if __name__ == "__main__":
    main()

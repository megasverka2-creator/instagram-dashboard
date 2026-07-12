#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse — AI Marketolog bot
================================
Telegram orqali suhbatlashadigan marketing maslahatchi.
Javoblarini umumiy bilimdan emas, KOMPANIYANING HAQIQIY ma'lumotidan quradi:

  • Savdo (kunlik, filial kesimida)      — savdo_data.enc.json
  • Eng ko'p sotilgan taomlar            — savdo_taomlar.enc.json
  • Buyurtma turlari (dostavka/zal)      — savdo_turlar.enc.json
  • Instagram statistikasi               — instagram_data.enc.json
  • Mijozlar izohlari tahlili            — izoh_tahlil.enc.json
  • Stop-list tarixi                     — stop_tahlil.enc.json

Fayllar GitHub'dagi shifrlangan nusxadan olinadi (sayt bilan bir xil parol).

Railway Variables:
  TELEGRAM_TOKEN     — @BotFather'dan olingan YANGI bot tokeni
  ANTHROPIC_API_KEY  — Claude API kaliti
  SAVDO_PAROL        — sayt paroli (shifrlangan fayllarni ochish uchun)
  RUXSAT_IDLAR       — vergul bilan ajratilgan Telegram ID'lar (kim yoza oladi)
  AI_MODEL           — ixtiyoriy (standart: claude-sonnet-5)
"""

import os
import json
import time
import base64
import hashlib
import traceback
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone

# ---------- Sozlamalar ----------
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
AI_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
PAROL = os.environ.get("SAVDO_PAROL", "")
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-5").strip()
RUXSAT_IDLAR = {s.strip() for s in os.environ.get("RUXSAT_IDLAR", "775946529").split(",") if s.strip()}

RAW = "https://raw.githubusercontent.com/megasverka2-creator/instagram-dashboard/main/"
TASHKENT = timezone(timedelta(hours=5))
KESH_MUDDATI = 6 * 3600          # ma'lumot keshi (6 soat)
TARIX_UZUNLIGI = 16              # suhbat xotirasi (xabarlar soni)
DAVR_KUN = 30                    # kontekstga kiradigan davr

API = f"https://api.telegram.org/bot{TOKEN}/"

# ---------- Telegram ----------
def tg(metod, params=None, timeout=40):
    try:
        data = urllib.parse.urlencode(params or {}).encode()
        req = urllib.request.Request(API + metod, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[tg] {metod} xato: {e}", flush=True)
        return {"ok": False}


def send(chat_id, text):
    """Uzun javobni Telegram limiti (4096) bo'yicha bo'lib yuborish."""
    while text:
        if len(text) <= 4000:
            bolak, text = text, ""
        else:
            kes = text.rfind("\n", 0, 4000)
            if kes < 500:
                kes = 4000
            bolak, text = text[:kes], text[kes:].lstrip("\n")
        tg("sendMessage", {"chat_id": chat_id, "text": bolak})


def yozmoqda(chat_id):
    tg("sendChatAction", {"chat_id": chat_id, "action": "typing"})


# ---------- Shifr ochish (sayt bilan bir xil sxema) ----------
def dekript(blob, parol):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt = base64.b64decode(blob["salt"])
    iv = base64.b64decode(blob["iv"])
    ct = base64.b64decode(blob["ct"])
    key = hashlib.pbkdf2_hmac("sha256", parol.encode(), salt, 150000, 32)
    return json.loads(AESGCM(key).decrypt(iv, ct, None).decode("utf-8"))


def enc_fayl(nomi):
    """GitHub'dan shifrlangan faylni olib ochish. Xatoda None."""
    try:
        req = urllib.request.Request(RAW + nomi + "?v=" + str(int(time.time())))
        with urllib.request.urlopen(req, timeout=60) as r:
            blob = json.loads(r.read().decode())
        return dekript(blob, PAROL) if blob.get("ct") else blob
    except Exception as e:
        print(f"[data] {nomi}: {e}", flush=True)
        return None


# ---------- Ma'lumot keshi ----------
DATA = {}
DATA_VAQT = 0


def data_yangila(majburiy=False):
    global DATA, DATA_VAQT
    if not majburiy and DATA and time.time() - DATA_VAQT < KESH_MUDDATI:
        return
    print("[data] yangilanmoqda...", flush=True)
    DATA = {
        "savdo": enc_fayl("savdo_data.enc.json"),
        "taomlar": enc_fayl("savdo_taomlar.enc.json"),
        "turlar": enc_fayl("savdo_turlar.enc.json"),
        "ig": enc_fayl("instagram_data.enc.json"),
        "izoh": enc_fayl("izoh_tahlil.enc.json"),
        "stop": enc_fayl("stop_tahlil.enc.json"),
    }
    DATA_VAQT = time.time()
    bor = [k for k, v in DATA.items() if v]
    print(f"[data] tayyor: {', '.join(bor) or 'hech narsa yuklanmadi!'}", flush=True)


# ---------- Kontekst quruvchilar (har biri xatoga chidamli) ----------
def mln(x):
    return f"{x/1e9:.2f} mlrd" if x >= 1e9 else (f"{x/1e6:.1f} mln" if x >= 1e6 else f"{int(x):,}".replace(",", " "))


def savdo_matn():
    S = DATA.get("savdo") or []
    if not isinstance(S, list) or not S:
        return ""
    kunlar = sorted(S, key=lambda d: d.get("date", ""))[-DAVR_KUN:]
    q = [f"--- SAVDO (oxirgi {len(kunlar)} kun, {kunlar[0]['date']} … {kunlar[-1]['date']}) ---"]
    fil = {}
    for d in kunlar:
        for dep, v in (d.get("departments") or {}).items():
            f = fil.setdefault(dep, [0, 0])
            f[0] += v.get("revenue", 0) or 0
            f[1] += v.get("checks", 0) or 0
    jami = sum(v[0] for v in fil.values())
    q.append(f"Jami tushum: {mln(jami)} so'm")
    for dep, (rev, chk) in sorted(fil.items(), key=lambda x: -x[1][0]):
        satr = f"  {dep}: {mln(rev)} so'm"
        if chk:
            satr += f", o'rtacha chek {int(rev/chk):,} so'm".replace(",", " ")
        q.append(satr)
    # Haftalik trend (oxirgi 7 kun vs oldingi 7 kun)
    if len(kunlar) >= 14:
        def summ(ks):
            return sum(v.get("revenue", 0) or 0 for d in ks for v in (d.get("departments") or {}).values())
        o, y = summ(kunlar[-14:-7]), summ(kunlar[-7:])
        if o > 0:
            q.append(f"Trend: oxirgi 7 kun {mln(y)} vs oldingi 7 kun {mln(o)} ({(y-o)/o*100:+.0f}%)")
    # Oxirgi 7 kun kunma-kun
    q.append("Oxirgi 7 kun (kun: tushum):")
    for d in kunlar[-7:]:
        rev = sum(v.get("revenue", 0) or 0 for v in (d.get("departments") or {}).values())
        q.append(f"  {d.get('date')}: {mln(rev)}")
    return "\n".join(q)


def taomlar_matn():
    T = DATA.get("taomlar") or {}
    deps = T.get("departments") if isinstance(T, dict) else None
    if not deps:
        return ""
    q = ["--- ENG KO'P SOTILGAN TAOMLAR (filial bo'yicha top 6) ---"]
    for dep, items in deps.items():
        top = sorted(items or [], key=lambda i: -(i.get("sum", 0) or 0))[:6]
        if top:
            q.append(f"{dep}: " + "; ".join(
                f"{i.get('dish')} ({mln(i.get('sum', 0))}, {i.get('amount', 0)} dona)" for i in top))
    return "\n".join(q)


def turlar_matn():
    T = DATA.get("turlar") or []
    if not isinstance(T, list) or not T:
        return ""
    fil = {}
    for d in T[-DAVR_KUN:]:
        for dep, node in (d.get("departments") or {}).items():
            f = fil.setdefault(dep, [0, 0, 0])   # [dostavka, zal, olib]
            for kind, v in (node or {}).items():
                r = (v or {}).get("revenue", 0) or 0
                if kind == "dostavka":
                    f[0] += r
                elif kind == "olib_ketish":
                    f[2] += r
                else:
                    f[1] += r
    if not fil:
        return ""
    q = [f"--- BUYURTMA TURLARI (oxirgi {DAVR_KUN} kun, filial kesimida) ---"]
    jd = jz = jo = 0
    for dep, (do, za, ol) in sorted(fil.items(), key=lambda x: -sum(x[1])):
        tot = do + za + ol
        if not tot:
            continue
        jd += do; jz += za; jo += ol
        q.append(f"  {dep}: Dostavka {do/tot*100:.0f}%, Zal {za/tot*100:.0f}%, "
                 f"Olib ketish {ol/tot*100:.0f}% (jami {mln(tot)})")
    jt = jd + jz + jo
    if jt:
        q.append(f"  TARMOQ: Dostavka {jd/jt*100:.0f}%, Zal {jz/jt*100:.0f}%, Olib ketish {jo/jt*100:.0f}%")
    return "\n".join(q)


def ig_matn():
    """Instagram tuzilmasi qanday bo'lmasin — post'ga o'xshash lug'atlarni rekursiv yig'amiz."""
    IG = DATA.get("ig")
    if not IG:
        return ""
    postlar = []

    def skan(node, brend=""):
        if isinstance(node, dict):
            if any(k in node for k in ("caption", "like_count", "views", "reach")):
                postlar.append((brend, node))
                return
            for k, v in node.items():
                skan(v, brend or (k if isinstance(v, (list, dict)) else ""))
        elif isinstance(node, list):
            for v in node:
                skan(v, brend)

    skan(IG)
    if not postlar:
        return ""

    def sana(p):
        return str(p[1].get("timestamp") or p[1].get("date") or p[1].get("sana") or "")

    postlar.sort(key=sana, reverse=True)
    q = ["--- INSTAGRAM (eng so'nggi postlar) ---"]
    for brend, p in postlar[:12]:
        cap = (p.get("caption") or "").replace("\n", " ")[:55]
        kors = p.get("views") or p.get("reach") or p.get("like_count") or 0
        q.append(f"  [{brend}] {sana((brend, p))[:10]} \"{cap}\" — {kors:,} ko'rish/qamrov".replace(",", " "))
    return "\n".join(q)


def izoh_matn():
    I = DATA.get("izoh")
    if not I:
        return ""
    matn = json.dumps(I, ensure_ascii=False) if not isinstance(I, str) else I
    return "--- MIJOZLAR IZOHLARI TAHLILI (tayyor AI xulosa) ---\n" + matn[:1800]


def _stop_ustun(qator, kalitlar):
    """Qator ichidan mos ustun nomini topadi (jadval tuzilishiga bog'lanmaslik uchun)."""
    if not qator:
        return None
    nomlar = list(qator.keys())
    for k in kalitlar:
        for nom in nomlar:
            if k in nom.lower():
                return nom
    return None


def _stop_son(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def stop_matn():
    S = DATA.get("stop")
    if not S:
        return ""
    q = [f"--- STOP-LIST (oxirgi {S.get('davr_kun', 14)} kun; ta'sir raqamlari DOIM taxminiy) ---"]

    # Yangi format (stop_sayt_collector): stop_kunlik={"qatorlar":[...]}; eskisi: kunlik=[...]
    rows = (S.get("stop_kunlik") or {}).get("qatorlar") or S.get("kunlik") or []
    if rows:
        filial_k = _stop_ustun(rows[0], ["filial", "dept", "bolim", "bo'lim", "branch"])
        taom_k = _stop_ustun(rows[0], ["taom", "mahsulot", "dish", "product", "nom"])
        soat_k = _stop_ustun(rows[0], ["soat", "hour", "davomiy", "daqiqa", "minut"])
        taxmin_k = _stop_ustun(rows[0], ["taxmin", "tasir", "ta'sir", "impact", "zarar", "summa"])

        # Filiallar kesimi
        fil = {}
        for r in rows:
            f = fil.setdefault(r.get(filial_k) if filial_k else "Noma'lum", [0, 0.0, 0.0])
            f[0] += 1
            f[1] += _stop_son(r.get(soat_k)) if soat_k else 0
            f[2] += _stop_son(r.get(taxmin_k)) if taxmin_k else 0
        q.append("Filiallar kesimi:")
        for f, (son, soat, tx) in sorted(fil.items(), key=lambda x: -x[1][0]):
            s = f"  {f}: {son} yozuv"
            if soat:
                s += f", ~{soat:.0f} soat stopda"
            if tx:
                s += f", taxminiy ta'sir ~{mln(tx)} so'm"
            q.append(s)

        # Eng ko'p stopga tushgan taomlar
        if taom_k:
            tm = {}
            for r in rows:
                nom = r.get(taom_k)
                if nom:
                    tm[nom] = tm.get(nom, 0) + 1
            top = sorted(tm.items(), key=lambda x: -x[1])[:10]
            if top:
                q.append("Eng ko'p stopga tushganlar: " + "; ".join(f"{n} ({s} marta)" for n, s in top))
    else:
        q.append("(Oxirgi davr uchun stop yozuvlari yo'q.)")

    # Sabablar — ikkala format
    sab_rows = (S.get("stop_sabablar") or {}).get("qatorlar") or S.get("sabablar") or []
    if sab_rows and isinstance(sab_rows[0], dict):
        sabab_k = _stop_ustun(sab_rows[0], ["sabab", "reason", "izoh", "matn"])
        if sabab_k:
            sm = {}
            for r in sab_rows:
                v = r.get(sabab_k)
                if v:
                    kalit = str(v)[:60]
                    sm[kalit] = sm.get(kalit, 0) + int(_stop_son(r.get("soni")) or 1)
            top = sorted(sm.items(), key=lambda x: -x[1])[:8]
            if top:
                q.append("Sabablar: " + "; ".join(f"{n} — {s}" for n, s in top))
    if S.get("erkin"):
        q.append("Yozma sabablar: " + "; ".join(e["matn"] for e in S["erkin"][:5]))
    q.append("(Stop ta'siri — taxminiy baho.)")
    return "\n".join(q)


def kontekst():
    bolaklar = [f"Bugun: {datetime.now(TASHKENT):%Y-%m-%d %A}"]
    for fn in (savdo_matn, taomlar_matn, turlar_matn, stop_matn, ig_matn, izoh_matn):
        try:
            m = fn()
            if m:
                bolaklar.append(m)
        except Exception as e:
            print(f"[kontekst] {fn.__name__}: {e}", flush=True)
    return "\n\n".join(bolaklar)


# ---------- AI ----------
def system_prompt():
    return (
        "Sen RestoPulse guruhining AI marketologisan. Toshkentdagi restoranlar tarmog'i "
        "(Benison-MegaCenter, Benison-Oila, Smart City, Eddo, Mazzona filiallari) marketing "
        "bo'limiga maslahat berasan.\n\n"
        "QAT'IY QOIDALAR:\n"
        "- Har xulosani BERILGAN MA'LUMOTdagi aniq raqamga tayan va o'sha raqamni ayt. "
        "Ma'lumotda yo'q narsani bilaman deb ko'rsatma — ochiq ayt: \"buni ma'lumotdan ko'ra olmayman\".\n"
        "- Reklama xarajatlari, target byudjeti, raqobatchilar ma'lumoti senda YO'Q — ROI haqida "
        "aniq da'vo qilma, faqat mavjud raqamlardagi bog'lanishlarni ko'rsat.\n"
        "- Stop-list ta'siri TAXMINIY baho — doim \"taxminan\" deb ayt.\n"
        "- Amaliy bo'l: umumiy nazariya emas, shu tarmoq raqamlariga mos aniq qadamlar taklif qil.\n"
        "- O'zbek tilida, samimiy va qisqa yoz. Oddiy matn (markdown belgilarsiz). "
        "Javob odatda 150-300 so'z; chuqur tahlil so'ralsa uzunroq mumkin.\n"
        "- Maqtov uchun maqtama; muammoni ham, imkoniyatni ham ochiq ayt.\n\n"
        "KOMPANIYA MA'LUMOTI (yangilangan avtomatik):\n\n" + kontekst()
    )


def ai_javob(tarix):
    body = json.dumps({
        "model": AI_MODEL,
        "max_tokens": 2500,
        "system": system_prompt(),
        "messages": list(tarix),
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": AI_KEY,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=180) as r:
        j = json.loads(r.read().decode())
    return "\n".join(c.get("text", "") for c in j.get("content", []) if c.get("type") == "text").strip()


# ---------- Suhbat xotirasi ----------
TARIXLAR = {}   # chat_id -> deque[{role, content}]


def tarix(chat_id):
    return TARIXLAR.setdefault(chat_id, deque(maxlen=TARIX_UZUNLIGI))


# ==================================================================
#                    POST MODULI (rasm → kanal)
# ==================================================================
import re
import uuid
from io import BytesIO

KANAL = os.environ.get("KANAL", "@benison_uz")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-image").strip()
PENDING = {}   # chat_id -> tayyorlanayotgan post

FOTO_PROMPT = (
    "A professional high-resolution food photograph with soft studio lighting. "
    "Enhance the dish colors to make it look more appetizing while keeping natural textures. "
    "Replace the original background with a clean warm dark slate surface with subtle texture "
    "(slightly lighter than charcoal). Slightly increase contrast and sharpness to highlight "
    "the details of the food. Keep the framing centered, show the full plate clearly, with the "
    "food in focus and the background minimalistic and softly blurred. "
    "Composition: the plate must be perfectly centered horizontally and positioned "
    "slightly ABOVE the vertical center, with the bottom quarter of the frame left as "
    "clean empty background (a caption bar will cover it). Show the ENTIRE plate — "
    "do not crop its edges. Style: restaurant menu photography, premium quality. "
    "IMPORTANT: do not alter the food itself — keep all ingredients, portions and plating "
    "exactly as in the original photo. Do not add any text, logos or watermarks."
)

MANZILLAR = (
    "📍 Filiallarimiz manzillari:\n"
    "Zarafshon:\n"
    "• Mega Center, 2-qavat (1-kichik tuman)\n"
    "• Oila savdo markazi, 2-qavat (12-kichik tuman)\n"
    "Uchquduq:\n"
    "• Smart City, 3-qavat (11-kichik tuman)\n\n"
    "Ijtimoiy tarmoqlarda bizni kuzatib boring — yangiliklar, aksiyalar va "
    "yoqimli videolar sizni kutmoqda!\n"
    '<a href="https://t.me/benison_uz">Telegram</a> | '
    '<a href="https://instagram.com/benison_uz">Instagram</a>'
)


def tg_multipart(metod, fields, fayl_nomi, fayl_bytes):
    """Telegram'ga fayl yuborish (sendPhoto va h.k.)."""
    b = uuid.uuid4().hex
    qism = []
    for k, v in fields.items():
        qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"photo\"; "
                f"filename=\"{fayl_nomi}\"\r\nContent-Type: image/png\r\n\r\n".encode())
    qism.append(fayl_bytes)
    qism.append(f"\r\n--{b}--\r\n".encode())
    req = urllib.request.Request(API + metod, data=b"".join(qism),
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        try:
            xato = e.read().decode()[:300]
        except Exception:
            xato = str(e)
        print(f"[tg] {metod} xato: {xato}", flush=True)
        return {"ok": False, "tavsif": xato}


def foto_yukla(file_id):
    """Telegram'dan foto baytlarini olish."""
    r = tg("getFile", {"file_id": file_id})
    yol = r.get("result", {}).get("file_path")
    if not yol:
        return None
    with urllib.request.urlopen(f"https://api.telegram.org/file/bot{TOKEN}/{yol}", timeout=90) as f:
        return f.read()


def menyu_narxlar():
    """iiko savdo ma'lumotidan: taom nomi -> o'rtacha sotuv narxi (1000 ga yaxlitlangan)."""
    T = DATA.get("taomlar") or {}
    jam = {}
    for dep, items in (T.get("departments") or {}).items():
        for i in items or []:
            n = (i.get("dish") or "").strip()
            s = i.get("sum", 0) or 0
            a = i.get("amount", 0) or 0
            if n and a > 0:
                st = jam.setdefault(n, [0.0, 0])
                st[0] += s
                st[1] += a
    return {n: max(1000, int(round(s / a / 1000)) * 1000) for n, (s, a) in jam.items() if a}


def rasm_kichraytir(foto_bytes, maks=1400):
    """Vision uchun rasmni kichraytirish (tez va arzon bo'lsin)."""
    try:
        from PIL import Image
        im = Image.open(BytesIO(foto_bytes)).convert("RGB")
        if max(im.size) > maks:
            k = maks / max(im.size)
            im = im.resize((int(im.width * k), int(im.height * k)))
        out = BytesIO()
        im.save(out, "JPEG", quality=88)
        return out.getvalue()
    except Exception:
        return foto_bytes


def taom_taxmin(foto_bytes):
    """Claude ko'zi bilan taomni aniqlash + savdo ma'lumotidan narx.
    Qaytaradi: (menyudagi_nom, narx) yoki (erkin_nom, None) yoki None."""
    data_yangila()
    narxlar = menyu_narxlar()
    royxat = sorted(narxlar.keys())[:300]
    s = ("Rasmda restoran taomi bor. Quyidagi menyu ro'yxatidan eng mos taom nomini top "
         "va javobda FAQAT o'sha nomni AYNAN ro'yxatdagidek yoz (boshqa hech narsa yozma). "
         "Ro'yxatda mos taom yo'q deb hisoblasang, taomning qisqa nomini o'zing yozib, "
         "oxiriga ? belgisi qo'y.\n\nMENYU:\n" + "\n".join(royxat))
    try:
        body = json.dumps({
            "model": AI_MODEL, "max_tokens": 100, "system": s,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                             "data": base64.b64encode(rasm_kichraytir(foto_bytes)).decode()}},
                {"type": "text", "text": "Bu qaysi taom?"},
            ]}],
        }).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
                                     headers={"content-type": "application/json", "x-api-key": AI_KEY,
                                              "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=90) as r:
            j = json.loads(r.read().decode())
        nom = "".join(c.get("text", "") for c in j.get("content", []) if c.get("type") == "text").strip()
        nom = nom.strip("«»\"'.")
        if not nom:
            return None
        if nom.endswith("?"):
            return nom.rstrip("? ").strip(), None
        if nom in narxlar:
            return nom, narxlar[nom]
        # yaqin moslik (harf farqlariga chidamli)
        import difflib
        yaqin = difflib.get_close_matches(nom, list(narxlar.keys()), n=1, cutoff=0.75)
        if yaqin:
            return yaqin[0], narxlar[yaqin[0]]
        return nom, None
    except Exception as e:
        print("[taxmin] xato:", e, flush=True)
        return None


AISHA_KEY = os.environ.get("AISHA_API_KEY", "").strip()

TEZ_SAVOLLAR = {
    "📊 Kecha savdo": "Kechagi savdo qanday bo'ldi? Filiallar kesimida qisqa xulosa ber.",
    "📈 Hafta xulosasi": "Oxirgi 7 kun savdosi qanday? Trend, eng yaxshi va xavotirli filialni ayt.",
    "🛑 Stop holati": "Stop-list holati qanday? Qaysi filialda muammo ko'p, taxminiy ta'siri qancha?",
    "🍽 Top taomlar": "Eng ko'p sotilayotgan taomlar qaysi? Filiallar bo'yicha qisqa ayt.",
}


def aisha_stt(audio_bytes):
    """Aisha AI: o'zbekcha ovozni matnga aylantirish (sync, qisqa audio)."""
    if not AISHA_KEY:
        return None
    try:
        b = uuid.uuid4().hex
        qism = []
        for k, v in [("language", "uz"), ("has_diarization", "false")]:
            qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"audio\"; "
                    f"filename=\"ovoz.ogg\"\r\nContent-Type: audio/ogg\r\n\r\n".encode())
        qism.append(audio_bytes)
        qism.append(f"\r\n--{b}--\r\n".encode())
        req = urllib.request.Request(
            "https://back.aisha.group/api/v1/stt/post/", data=b"".join(qism),
            headers={"Content-Type": f"multipart/form-data; boundary={b}",
                     "X-Api-Key": AISHA_KEY})
        with urllib.request.urlopen(req, timeout=120) as r:
            j = json.loads(r.read().decode())
        return (j.get("transcript") or "").strip() or None
    except Exception as e:
        try:
            print("[aisha] xato:", e.read().decode()[:300], flush=True)
        except Exception:
            print("[aisha] xato:", e, flush=True)
        return None


def izoh_ajrat(caption):
    """'Juvava, 58000' yoki 'Qiyma shashlik 3+1, 69000, 92000' -> (taom, narx, eski).
    «Qovurma lag'mon, 68.000 so'm» kabi yozuvlar ham qabul qilinadi."""
    if not caption:
        return None
    # tozalash: qo'shtirnoqlar va valyuta so'zlari (taom nomidagi ' apostrofga tegmaymiz)
    c = re.sub(r"[«»\"“”]", " ", caption)
    c = re.sub(r"(?i)\b(so['’ʻ`]?m|сум|сўм|uzs)\b", " ", c)
    # boshqaruv so'zlari nomga kirmasin (faqat lotincha — kirillcha nomlar daxlsiz)
    c = re.sub(r"(?i)\b(panel|v[12]|yangilik|aksiya|mavsumiy|kombo)\b", " ", c)
    qismlar = [q.strip() for q in re.split(r"[,;\n]", c) if q.strip()]
    narxlar, nom_qismlar = [], []
    for q in qismlar:
        raqam = re.sub(r"[\s.]", "", q)
        if raqam.isdigit() and 1000 <= int(raqam) <= 10_000_000:
            narxlar.append(int(raqam))
        else:
            nom_qismlar.append(q)
    if not narxlar and nom_qismlar:
        # vergulsiz yozilgan: «Napoleon shashlik 35 000» — nom oxiridagi raqamni ajratamiz
        m2 = re.search(r"^(.*?)(\d[\d\s.]{3,}|\d{4,})\s*$", nom_qismlar[-1])
        if m2:
            raqam = re.sub(r"[\s.]", "", m2.group(2))
            if raqam.isdigit() and 1000 <= int(raqam) <= 10_000_000:
                narxlar.append(int(raqam))
                nom_qismlar[-1] = m2.group(1).strip()
    taom = " ".join(q for q in nom_qismlar if q).strip(" -–—,")
    if not taom or not narxlar:
        return None
    narx = narxlar[0]
    eski = narxlar[1] if len(narxlar) > 1 else None
    if eski and eski < narx:
        narx, eski = eski, narx
    return taom, narx, eski


OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1.5").strip()


def openai_tahrir(foto_bytes):
    """GPT Image (ChatGPT'dagi model) bilan taom fotosini tahrirlash.
    Xatoda None — zanjir Gemini yoki kod-tahrirga o'tadi."""
    if not OPENAI_KEY:
        return None
    try:
        # OpenAI ba'zi JPEG'larni rad etadi — toza PNG'ga qayta kodlaymiz
        from PIL import Image
        im = Image.open(BytesIO(foto_bytes)).convert("RGB")
        if max(im.size) > 2048:
            k = 2048 / max(im.size)
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        png = BytesIO()
        im.save(png, "PNG")
        png_bytes = png.getvalue()

        b = uuid.uuid4().hex
        qism = []
        for k, v in [("model", OPENAI_IMAGE_MODEL), ("prompt", FOTO_PROMPT),
                     ("size", "1024x1536"), ("quality", "medium"),
                     ("input_fidelity", "high")]:
            qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        qism.append(f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; "
                    f"filename=\"taom.png\"\r\nContent-Type: image/png\r\n\r\n".encode())
        qism.append(png_bytes)
        qism.append(f"\r\n--{b}--\r\n".encode())
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/edits", data=b"".join(qism),
            headers={"Content-Type": f"multipart/form-data; boundary={b}",
                     "Authorization": f"Bearer {OPENAI_KEY}"})
        with urllib.request.urlopen(req, timeout=240) as r:
            j = json.loads(r.read().decode())
        d = (j.get("data") or [{}])[0].get("b64_json")
        if d:
            return base64.b64decode(d)
        print("[openai] javobda rasm yo'q:", str(j)[:200], flush=True)
    except Exception as e:
        try:
            print("[openai] xato:", e.read().decode()[:300], flush=True)
        except Exception:
            print("[openai] xato:", e, flush=True)
    return None


def nano_banana(foto_bytes):
    """Gemini (Nano Banana) bilan taom fotosini professional qilish.
    Xatoda None — kartochka asl foto bilan yasaladi."""
    if not GEMINI_KEY:
        return None
    try:
        body = json.dumps({
            "contents": [{"parts": [
                {"text": FOTO_PROMPT},
                {"inline_data": {"mime_type": "image/jpeg",
                                 "data": base64.b64encode(foto_bytes).decode()}},
            ]}],
        }).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            data=body, headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY})
        with urllib.request.urlopen(req, timeout=180) as r:
            j = json.loads(r.read().decode())
        for p in j.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            d = p.get("inline_data") or p.get("inlineData")
            if d and d.get("data"):
                return base64.b64decode(d["data"])
        print("[nano] javobda rasm yo'q:", str(j)[:200], flush=True)
    except Exception as e:
        try:
            print("[nano] xato:", e.read().decode()[:300], flush=True)
        except Exception:
            print("[nano] xato:", e, flush=True)
    return None


# ---------- Kartochka (aralash shablon: to'liq foto + yashil narx paneli) ----------
KW, KH = 1080, 1350
TEAL, TEAL_TO = (18, 115, 105), (13, 86, 79)   # brendbuk: HEX #127369
CREAM, RED = (245, 240, 230), (196, 57, 46)


def _font(w, size):
    from PIL import ImageFont
    yol = os.path.dirname(os.path.abspath(__file__))
    exo = os.path.join(yol, "Exo2.ttf")
    if os.path.exists(exo):                      # brendbuk shrifti (variable)
        f = ImageFont.truetype(exo, size)
        try:
            f.set_variation_by_name(w)
            return f
        except Exception:
            pass
    return ImageFont.truetype(os.path.join(yol, f"Montserrat-{w}.ttf"), size)


def _mos_font(d, matn, w, boshl, max_w, min_size=44):
    s = boshl
    while s > min_size:
        f = _font(w, s)
        if d.textbbox((0, 0), matn, font=f)[2] <= max_w:
            return f
        s -= 4
    return _font(w, min_size)


def _oq_logo(h):
    from PIL import Image
    yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    im = Image.open(yol).convert("RGBA")
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    oq = Image.new("RGBA", im.size, (255, 255, 255, 0))
    oq.putalpha(im.getchannel("A"))
    return oq


def _teg_chiz(d, teg):
    f_t = _font("ExtraBold", 40)
    bb = d.textbbox((0, 0), teg, font=f_t)
    tx = KW - 56 - bb[2] - 68
    d.rounded_rectangle([tx, 52, KW-56, 52+bb[3]-bb[1]+36],
                        radius=16, fill=RED if teg == "AKSIYA" else TEAL)
    d.text((tx+34, 70-bb[1]), teg, font=f_t, fill=(255, 255, 255))


def _nom_chiz(d, taom, x, y, max_w, rang, boshl=64):
    """Nomni sig'diradi: kichraytiradi, bo'lmasa 2 qatorga. Balandlikni qaytaradi."""
    s = boshl
    while s > 50:
        if d.textbbox((0, 0), taom, font=_font("Black", s))[2] <= max_w:
            d.text((x, y), taom, font=_font("Black", s), fill=rang)
            return s + 10
        s -= 4
    sozlar = taom.split()
    for i in range(len(sozlar), 0, -1):
        if d.textbbox((0, 0), " ".join(sozlar[:i]), font=_font("Black", 50))[2] <= max_w:
            q1, q2 = " ".join(sozlar[:i]), " ".join(sozlar[i:])
            break
    else:
        q1, q2 = taom, ""
    d.text((x, y), q1, font=_font("Black", 50), fill=rang)
    if q2:
        s2 = 50
        while s2 > 38 and d.textbbox((0, 0), q2, font=_font("Black", s2))[2] > max_w:
            s2 -= 4
        d.text((x, y + 58), q2, font=_font("Black", s2), fill=rang)
        return 58 + s2 + 12
    return 62


def _foto_moslashtir(foto_bytes):
    from PIL import Image
    foto = Image.open(BytesIO(foto_bytes)).convert("RGB")
    k = max(KW / foto.width, KH / foto.height)
    foto = foto.resize((int(foto.width * k) + 1, int(foto.height * k) + 1), Image.LANCZOS)
    x = (foto.width - KW) // 2
    y = min(foto.height - KH, (foto.height - KH) // 2 + int(KH * 0.06))
    return foto.crop((x, max(0, y), x + KW, max(0, y) + KH))


def kartochka_yasa(foto_bytes, taom, narx, eski=None, teg=None, uslub="v2"):
    """V2 «Chip» (standart): to'liq foto + teal narx-chip.
    V1 «Panel»: pastda brend panel (izohga 'panel' yozilsa)."""
    from PIL import Image, ImageDraw, ImageFilter
    im = _foto_moslashtir(foto_bytes)
    d = ImageDraw.Draw(im, "RGBA")
    if teg is None and eski:
        teg = "AKSIYA"
    nm = f"{narx:,}".replace(",", " ")

    if uslub == "v1":
        PANEL = 320
        for i in range(40):
            d.line([(0, KH-PANEL-40+i), (KW, KH-PANEL-40+i)], fill=TEAL + (int(255*i/40),))
        for i in range(PANEL):
            t = i / PANEL
            col = tuple(int(TEAL[j] + (TEAL_TO[j]-TEAL[j])*t) for j in range(3))
            d.line([(0, KH-PANEL+i), (KW, KH-PANEL+i)], fill=col)
        naqsh_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "naqsh.png")
        if os.path.exists(naqsh_yol):
            n = Image.open(naqsh_yol).convert("RGBA").crop((0, 0, KW, PANEL))
            im2 = im.convert("RGBA")
            im2.alpha_composite(n, (0, KH-PANEL))
            im = im2.convert("RGB")
            d = ImageDraw.Draw(im, "RGBA")
        d.rectangle([64, KH-PANEL+44, 64+96, KH-PANEL+52], fill=(255, 170, 60))
        _nom_chiz(d, taom, 64, KH-PANEL+70, KW-128, (255, 255, 255), boshl=68)
        f_n = _font("Black", 96)
        bb = d.textbbox((0, 0), nm, font=f_n)
        ny = KH - 118 - bb[3]
        if eski:
            em = f"{eski:,}".replace(",", " ")
            f_e = _font("SemiBold", 44)
            eb = d.textbbox((0, 0), em, font=f_e)
            d.text((64, ny-46), em, font=f_e, fill=(208, 224, 219))
            d.line([(58, ny-20), (64+eb[2]+6, ny-20)], fill=RED, width=6)
        d.text((64, ny), nm, font=f_n, fill=(255, 255, 255))
        d.text((64+bb[2]+18, ny+52), "so'm", font=_font("SemiBold", 38), fill=CREAM)
        logo = _oq_logo(52)
        im.paste(logo, (KW-64-logo.width, KH-96), logo)
    else:
        grad = Image.new("L", (1, KH), 0)
        for y in range(KH):
            t = max(0.0, (y - KH*0.52) / (KH*0.48))
            grad.putpixel((0, y), int(215 * t**1.5))
        im = Image.composite(Image.new("RGB", (KW, KH), (8, 22, 20)), im, grad.resize((KW, KH)))
        d = ImageDraw.Draw(im, "RGBA")
        yh = _nom_chiz(d, taom, 64, KH-300, KW-128, (255, 255, 255), boshl=76)
        d.text((64, KH-300+yh+6), "@benison_uz", font=_font("SemiBold", 32), fill=(215, 220, 218))
        matn = nm + " so'm"
        f_n = _font("ExtraBold", 56)
        bb = d.textbbox((0, 0), matn, font=f_n)
        cw, ch = bb[2]+76, bb[3]-bb[1]+48
        cx, cy = KW-64-cw, KH-84-ch
        soya = Image.new("RGBA", (cw+40, ch+40), (0, 0, 0, 0))
        ImageDraw.Draw(soya).rounded_rectangle([20, 20, cw+20, ch+20], radius=26, fill=(0, 0, 0, 110))
        im.paste(Image.new("RGB", soya.size, (0, 0, 0)), (cx-20, cy-14),
                 soya.filter(ImageFilter.GaussianBlur(10)))
        d.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=26, fill=TEAL)
        d.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=26, outline=(255, 255, 255, 70), width=2)
        d.text((cx+38, cy+24-bb[1]), matn, font=f_n, fill=(255, 255, 255))
        if eski:
            em = f"{eski:,}".replace(",", " ")
            f_e = _font("SemiBold", 44)
            eb = d.textbbox((0, 0), em, font=f_e)
            ex = cx - eb[2] - 34
            d.text((ex, cy+ch//2-26), em, font=f_e, fill=(232, 232, 228))
            d.line([(ex-6, cy+ch//2), (ex+eb[2]+6, cy+ch//2)], fill=RED, width=6)
    logo2 = _oq_logo(56)
    im.paste(logo2, (56, 56), logo2)
    d = ImageDraw.Draw(im, "RGBA")
    if teg:
        _teg_chiz(d, teg)
    chiqish = BytesIO()
    im.convert("RGB").save(chiqish, "PNG")
    return chiqish.getvalue()


def post_matn_yoz(taom, narx, eski=None, teg=None):
    """Kanal uslubida post matni (Claude). Manzillar bloki alohida qo'shiladi."""
    narx_q = (f"Narxi: {eski:,} → {narx:,} so'm (chegirma!)" if eski
              else f"Narxi: {narx:,} so'm").replace(",", " ")
    s = ("Sen Benison restorani (O'zbekiston) Telegram kanali uchun post yozasan. "
         "Kanal uslubi namunalari:\n"
         "1) «Benison menyusida mazali yangiliklar davom etadi! Uyg'ur taomlarining o'ziga xos "
         "ta'mi endi siz uchun yanada yaqin — Juvava! Mayin xamir, shirali go'sht, rang-barang "
         "sabzavotlar va maxsus sous uyg'unligi bir laganda jam bo'ldi. Narxi: 58 000 so'm. "
         "Yaqinlaringiz bilan kelib, Benisonda mazali taomlardan bahramand bo'ling!»\n"
         "2) «BENISON'DAN MAXSUS 3+1 TAKLIFI! Faqat 2 kun, barcha filiallarimiz uchun! ...»\n\n"
         f"QOIDALAR: taom nomini AYNAN berilganidek yoz — «{taom}» — bironta harfini o'zgartirma, tarjima qilma, qisqartirma; faqat o'zbekcha; 3-4 qisqa xatboshi; 2-3 ta o'rinli emoji; narx qatorini "
         f"AYNAN shunday yoz: «{narx_q}»; manzillarni YOZMA (alohida qo'shiladi); 600 belgidan "
         "oshma; taom tarkibini bilmasang umumiy ishtaha ochuvchi tavsif ber, o'ylab tarkib to'qima.")
    body = json.dumps({
        "model": AI_MODEL, "max_tokens": 800, "system": s,
        "messages": [{"role": "user", "content": f"Taom: {taom}. " + (
            "Aksiya posti (chegirma bor)." if (eski or teg == "AKSIYA") else
            "Yangilik posti — menyuga YANGI qo'shilgan taom." if teg == "YANGILIK" else
            "Kombo/to'plam taklifi posti." if teg == "KOMBO" else
            "Mavsumiy taklif posti." if teg == "MAVSUMIY" else
            "Oddiy taom posti: bu taom menyuda ALLAQACHON bor — uni 'yangilik' dema, "
            "shunchaki ishtaha ochadigan, taomni sog'intiradigan tanishtiruv yoz.")}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
                                 headers={"content-type": "application/json", "x-api-key": AI_KEY,
                                          "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode())
    return "\n".join(c.get("text", "") for c in j.get("content", []) if c.get("type") == "text").strip()


def kod_tahrir(foto_bytes):
    """Bepul zaxira tahrir (Nano Banana ishlamasa): ranglarni jonlantirish,
    kontrast/tiniqlik, iliq ton va yengil vinyetka. AI emas — lekin xom rasmdan yaxshi."""
    try:
        from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
        im = Image.open(BytesIO(foto_bytes)).convert("RGB")
        im = ImageEnhance.Color(im).enhance(1.18)        # ranglar jonliroq
        im = ImageEnhance.Contrast(im).enhance(1.12)     # kontrast
        im = ImageEnhance.Brightness(im).enhance(1.04)   # ozgina yorug'roq
        im = ImageEnhance.Sharpness(im).enhance(1.35)    # tiniqlik
        # iliq ton (qizil +, ko'k -)
        r, g, b = im.split()
        r = r.point(lambda x: min(255, int(x * 1.04)))
        b = b.point(lambda x: int(x * 0.97))
        im = Image.merge("RGB", (r, g, b))
        # yengil vinyetka — e'tibor markazga
        w, h = im.size
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse([-int(w*0.25), -int(h*0.25), int(w*1.25), int(h*1.25)], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.18)))
        qora = ImageEnhance.Brightness(im).enhance(0.72)
        im = Image.composite(im, qora, mask)
        chiqish = BytesIO()
        im.save(chiqish, "JPEG", quality=92)
        return chiqish.getvalue()
    except Exception as e:
        print("[kod-tahrir] xato:", e, flush=True)
        return foto_bytes


def uslub_aniqla(caption):
    c = (caption or "").lower()
    if "panel" in c or c.startswith("v1") or " v1" in c:
        return "v1"
    return "v2"


def teg_aniqla(caption, eski):
    """Izohdagi kalit so'zdan tegni aniqlash: aksiya/kombo/mavsumiy/yangilik."""
    c = (caption or "").lower()
    for soz, teg in [("aksiya", "AKSIYA"), ("kombo", "KOMBO"),
                     ("mavsum", "MAVSUMIY"), ("yangilik", "YANGILIK")]:
        if soz in c:
            return teg
    return "AKSIYA" if eski else None   # so'z yozilmasa — teg chiqmaydi (oddiy taom)


def post_tayyorla(chat_id, foto_bytes, taom, narx, eski, teg=None, uslub="v2"):
    """To'liq quvur: Nano Banana → kartochka → matn → preview."""
    send(chat_id, "🍳 Rasm qayta ishlanmoqda...")
    yaxshi = openai_tahrir(foto_bytes) or nano_banana(foto_bytes)
    if not yaxshi:
        yaxshi = kod_tahrir(foto_bytes)
        send(chat_id, "ℹ️ AI tahrir hozircha yo'q — bepul kod-tahrir qo'llandi "
                      "(ranglar, kontrast, vinyetka).")
    kartochka = kartochka_yasa(yaxshi or foto_bytes, taom, narx, eski, teg, uslub)
    yozmoqda(chat_id)
    try:
        matn = post_matn_yoz(taom, narx, eski, teg)
    except Exception as e:
        print("[post] matn xatosi:", e, flush=True)
        matn = f"{taom} — endi Benisonda! 😋\n\nNarxi: {narx:,} so'm".replace(",", " ")
    caption = matn + "\n\n" + MANZILLAR
    PENDING[chat_id] = {"asl": foto_bytes, "kartochka": kartochka, "teg": teg, "uslub": uslub,
                        "taom": taom, "narx": narx, "eski": eski, "caption": caption}
    tugmalar = json.dumps({"inline_keyboard": [
        [{"text": "✅ Kanalga chiqarish", "callback_data": "post_ok"}],
        [{"text": "🔄 Rasmni qayta ishlash", "callback_data": "post_rasm"},
         {"text": "✏️ Matnni qayta yozish", "callback_data": "post_matn"}],
        [{"text": "❌ Bekor qilish", "callback_data": "post_bekor"}],
    ]})
    tg_multipart("sendPhoto", {"chat_id": chat_id, "caption": caption[:1024],
                               "parse_mode": "HTML", "reply_markup": tugmalar},
                 "post.png", kartochka)


def callback_qayta_ishla(cq):
    chat_id = cq["message"]["chat"]["id"]
    kimdan = str(cq.get("from", {}).get("id", ""))
    data = cq.get("data", "")
    tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
    if kimdan not in RUXSAT_IDLAR:
        return
    p = PENDING.get(chat_id)
    if not p:
        send(chat_id, "Bu post eskirgan — rasmni qaytadan yuboring.")
        return
    if data == "taxmin_ok":
        t = p.get("taxmin")
        fid = p.get("kutilmoqda")
        if not t or not fid:
            send(chat_id, "Eskirgan — rasmni qaytadan yuboring.")
            return
        foto = foto_yukla(fid)
        PENDING.pop(chat_id, None)
        if not foto:
            send(chat_id, "Rasmni yuklab bo'lmadi, qaytadan yuboring.")
            return
        post_tayyorla(chat_id, foto, t[0], t[1], None, teg=None)
        return
    if data == "taxmin_yoq":
        p.pop("taxmin", None)
        send(chat_id, "Yozing: Nomi, narxi (masalan: Juvava, 58000)")
        return
    if data == "post_bekor":
        PENDING.pop(chat_id, None)
        send(chat_id, "Bekor qilindi ❌")
    elif data == "post_ok":
        r = tg_multipart("sendPhoto", {"chat_id": KANAL, "caption": p["caption"][:1024],
                                       "parse_mode": "HTML"}, "post.png", p["kartochka"])
        if r.get("ok"):
            PENDING.pop(chat_id, None)
            send(chat_id, f"✅ Post {KANAL} kanaliga chiqdi!")
        else:
            sabab = r.get("tavsif", "nomalum xato")
            send(chat_id, f"Kanalga chiqmadi: {sabab}\n"
                          "Bot kanalda admin ekanini tekshiring.")
    elif data == "post_rasm":
        post_tayyorla(chat_id, p["asl"], p["taom"], p["narx"], p["eski"], p.get("teg"), p.get("uslub", "v2"))
    elif data == "post_matn":
        yozmoqda(chat_id)
        try:
            p["caption"] = post_matn_yoz(p["taom"], p["narx"], p["eski"], p.get("teg")) + "\n\n" + MANZILLAR
            tugmalar = json.dumps({"inline_keyboard": [
                [{"text": "✅ Kanalga chiqarish", "callback_data": "post_ok"}],
                [{"text": "🔄 Rasmni qayta ishlash", "callback_data": "post_rasm"},
                 {"text": "✏️ Matnni qayta yozish", "callback_data": "post_matn"}],
                [{"text": "❌ Bekor qilish", "callback_data": "post_bekor"}],
            ]})
            tg_multipart("sendPhoto", {"chat_id": chat_id, "caption": p["caption"][:1024],
                                       "parse_mode": "HTML", "reply_markup": tugmalar},
                         "post.png", p["kartochka"])
        except Exception as e:
            send(chat_id, f"Matn yozishda xato: {e}")


def foto_xabar(msg):
    """Foto/fayl keldi: izoh bo'lsa quvur, bo'lmasa taomni AI o'zi aniqlaydi."""
    chat_id = msg["chat"]["id"]
    if msg.get("photo"):
        file_id = msg["photo"][-1]["file_id"]
    else:                                     # fayl sifatida yuborilgan sifatli rasm
        file_id = msg["document"]["file_id"]
    tahlil = izoh_ajrat(msg.get("caption", ""))
    if not tahlil:
        send(chat_id, "🔎 Taomni aniqlayapman...")
        foto = foto_yukla(file_id)
        if not foto:
            send(chat_id, "Rasmni yuklab bo'lmadi, qaytadan yuboring.")
            return
        taxmin = taom_taxmin(foto)
        PENDING[chat_id] = {"kutilmoqda": file_id}
        if taxmin and taxmin[1]:
            nom, narx = taxmin
            PENDING[chat_id]["taxmin"] = (nom, narx)
            tugmalar = json.dumps({"inline_keyboard": [
                [{"text": f"✅ {nom} — {narx:,} so'm".replace(",", " "),
                  "callback_data": "taxmin_ok"}],
                [{"text": "✏️ O'zim yozaman", "callback_data": "taxmin_yoq"}],
            ]})
            tg("sendMessage", {"chat_id": chat_id, "reply_markup": tugmalar,
                               "text": f"Menimcha bu «{nom}» — savdo ma'lumotiga ko'ra "
                                       f"o'rtacha narxi ~{narx:,} so'm.".replace(",", " ") +
                                       "\nTo'g'ri bo'lsa tasdiqlang, yoki o'zingiz yozing "
                                       "(masalan: Juvava, 58000):"})
        else:
            qism = f"Bu «{taxmin[0]}»ga o'xshaydi, lekin narxini savdo ma'lumotidan topolmadim.\n" if taxmin else ""
            send(chat_id, "Rasm qabul qilindi 📸 " + qism +
                          "Taom nomi va narxini yozing:\n\n"
                          "Juvava, 58000\n"
                          "Aksiya: Qiyma shashlik 3+1, 69000, 92000\n"
                          "Teg so'zlari: yangilik / aksiya / kombo / mavsumiy")
        return
    foto = foto_yukla(file_id)
    if not foto:
        send(chat_id, "Rasmni yuklab bo'lmadi, qaytadan yuboring.")
        return
    post_tayyorla(chat_id, foto, *tahlil, teg=teg_aniqla(msg.get("caption", ""), tahlil[2]), uslub=uslub_aniqla(msg.get("caption", "")))


# ---------- Asosiy sikl ----------
def xabar_qayta_ishla(msg):
    chat_id = msg["chat"]["id"]
    kimdan = str(msg.get("from", {}).get("id", ""))
    matn = (msg.get("text") or "").strip()

    if kimdan not in RUXSAT_IDLAR:
        print(f"[ruxsat] begona ID: {kimdan}", flush=True)
        return
    ovoz = msg.get("voice") or msg.get("audio")
    if ovoz:
        yozmoqda(chat_id)
        audio = foto_yukla(ovoz["file_id"])
        matn = aisha_stt(audio) if audio else None
        if not matn:
            send(chat_id, "Ovozni matnga aylantirib bo'lmadi 😕 "
                          "(AISHA_API_KEY yoki balansni tekshiring), yozma yuboring.")
            return
        send(chat_id, f"🎤 «{matn}»")
        # endi matn oddiy yozma xabar kabi davom etadi
    if msg.get("photo"):
        foto_xabar(msg)
        return
    doc = msg.get("document") or {}
    if doc.get("mime_type", "") in ("image/jpeg", "image/png", "image/webp"):
        foto_xabar(msg)                       # fayl sifatidagi sifatli rasm
        return
    # oldin rasm yuborilgan, endi izoh kelgan bo'lsa
    p = PENDING.get(chat_id)
    if p and p.get("kutilmoqda") and matn and not matn.startswith("/"):
        tahlil = izoh_ajrat(matn)
        if not tahlil:
            send(chat_id, "Tushunmadim. Format: «Juvava, 58000» yoki "
                          "«Qiyma shashlik 3+1, 69000, 92000»")
            return
        foto = foto_yukla(p["kutilmoqda"])
        PENDING.pop(chat_id, None)
        if not foto:
            send(chat_id, "Rasmni yuklab bo'lmadi, qaytadan yuboring.")
            return
        post_tayyorla(chat_id, foto, *tahlil, teg=teg_aniqla(matn, tahlil[2]), uslub=uslub_aniqla(matn))
        return
    if not matn:
        send(chat_id, "Matn yozing yoki taom rasmini yuboring 📸")
        return

    if matn == "/start":
        klaviatura = json.dumps({"keyboard": [
            [{"text": "📊 Kecha savdo"}, {"text": "📈 Hafta xulosasi"}],
            [{"text": "🛑 Stop holati"}, {"text": "🍽 Top taomlar"}],
        ], "resize_keyboard": True, "is_persistent": True})
        tg("sendMessage", {"chat_id": chat_id, "reply_markup": klaviatura,
                           "text": "Tez savollar tugmalari yoqildi 👇"})
        send(chat_id,
             "Salom! Men RestoPulse AI marketologiman. 📊\n\n"
             "Menda kompaniyaning haqiqiy ma'lumotlari bor: savdo (filial kesimida), "
             "eng ko'p sotilgan taomlar, buyurtma turlari, Instagram statistikasi, "
             "mijozlar izohlari va stop-list tarixi.\n\n"
             "🎤 Ovozli xabar ham yuboravering — o'zim tushunib javob beraman "
             "(masalan: «kecha savdo qancha bo'ldi?»).\n\n"
             "Erkin savol beravering, masalan:\n"
             "• Keyingi hafta Mazzona uchun nima qilay?\n"
             "• Eddo'da dostavkani qanday oshiramiz?\n"
             "• Shu aksiya g'oyamni baholab ber: ...\n\n"
             "Buyruqlar: /yangila — ma'lumotni yangilash, /holat — ma'lumot holati.\n\n"
             "📸 POST YASASH: taom rasmini yuboring — taomni o'zim aniqlab, "
             "savdo ma'lumotidan narxini taklif qilaman. Yoki izohga o'zingiz yozing: "
             "«Nomi, narxi». Sifat uchun rasmni FAYL (hujjat) sifatida yuborsangiz ham bo'ladi.\n"
             "Teg so'zlari: yangilik / aksiya / kombo / mavsumiy (yozmasangiz — tegsiz).")
        return
    if matn == "/yangila":
        yozmoqda(chat_id)
        data_yangila(majburiy=True)
        bor = [k for k, v in DATA.items() if v]
        send(chat_id, "Ma'lumot yangilandi ✅ Mavjud: " + ", ".join(bor))
        return
    if matn == "/holat":
        data_yangila()
        yosh = int((time.time() - DATA_VAQT) / 60)
        bor = [k for k, v in DATA.items() if v]
        yoq = [k for k, v in DATA.items() if not v]
        send(chat_id, f"Ma'lumot yoshi: {yosh} daqiqa\nMavjud: {', '.join(bor) or '—'}"
                      + (f"\nYuklanmadi: {', '.join(yoq)}" if yoq else ""))
        return

    if matn == "/savdo":
        matn = TEZ_SAVOLLAR["📊 Kecha savdo"]
    matn = TEZ_SAVOLLAR.get(matn, matn)

    # Oddiy savol → AI
    yozmoqda(chat_id)
    data_yangila()
    t = tarix(chat_id)
    t.append({"role": "user", "content": matn})
    try:
        javob = ai_javob(t)
        if not javob:
            raise RuntimeError("bo'sh javob")
        t.append({"role": "assistant", "content": javob})
        send(chat_id, javob)
    except Exception as e:
        t.pop()   # muvaffaqiyatsiz so'rovni tarixdan olib tashlaymiz
        print(f"[ai] xato: {e}", flush=True)
        send(chat_id, "AI bilan bog'lanishda xato bo'ldi, birozdan keyin qayta urinib ko'ring.")


def main():
    if not TOKEN or not AI_KEY or not PAROL:
        print("XATO: TELEGRAM_TOKEN / ANTHROPIC_API_KEY / SAVDO_PAROL to'liq emas.", flush=True)
        return
    tg("setMyCommands", {"commands": json.dumps([
        {"command": "start", "description": "Bot haqida va tez tugmalar"},
        {"command": "savdo", "description": "Kechagi savdo xulosasi"},
        {"command": "yangila", "description": "Ma'lumotni yangilash"},
        {"command": "holat", "description": "Ma'lumot holati"},
    ])})
    print(f"[bot] AI Marketolog ishga tushdi. Ruxsat: {sorted(RUXSAT_IDLAR)}", flush=True)
    data_yangila()
    offset = 0
    while True:
        try:
            r = tg("getUpdates", {"offset": offset, "timeout": 50}, timeout=70)
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    try:
                        xabar_qayta_ishla(upd["message"])
                    except Exception:
                        traceback.print_exc()
                elif "callback_query" in upd:
                    try:
                        callback_qayta_ishla(upd["callback_query"])
                    except Exception:
                        traceback.print_exc()
        except Exception as e:
            print(f"[sikl] {e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()

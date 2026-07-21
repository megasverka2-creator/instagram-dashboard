#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RestoPulse AI IT-chi — TUZATUVCHI (2-daraja: AI taklif qiladi, odam tasdiqlaydi)
=================================================================================
Ish tartibi:
  1. Oxirgi YIQILGAN (failure) workflow run'ini topadi (yoki RUN_ID berilsa o'shani)
  2. Xato logini + workflow faylini + tegishli .py fayllarni yig'adi
  3. Claude tashxis qo'yadi; tuzatish mumkin bo'lsa — tuzatilgan fayl(lar)ni yozadi
  4. main'ga EMAS — yangi shoxga commit qilib, Pull Request ochadi
  5. Telegram'ga: tashxis + PR havolasi. Merge = tasdiq, Close = rad.

Xavfsizlik: faqat ruxsat etilgan kengaytmalar, .enc.json va .github/workflows
o'zgartirilmaydi (workflow tuzatish kerak bo'lsa — matnda tavsiya beradi),
maksimum 3 fayl. Hech qachon main'ga to'g'ridan-to'g'ri yozmaydi.

Sekretlar: ANTHROPIC_API_KEY, TELEGRAM_TOKEN. GITHUB_TOKEN — Actions beradi.
"""

import io
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "megasverka2-creator/instagram-dashboard")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("ITCHI_CHAT_ID", "775946529")
RUN_ID = os.environ.get("RUN_ID", "").strip()  # ixtiyoriy: aniq run'ni tuzatish
MODEL = "claude-opus-4-8"

OZIMIZ = ("AI IT-chi", "AI IT-chi tuzatuvchi")  # o'z-o'zini tuzatishga urinmasin
RUXSAT_KENGAYTMA = (".py", ".js", ".html", ".css", ".md", ".json", ".txt")
TAQIQ_QISM = (".enc.json", ".github/workflows", "shifr.py")
MAX_FAYL = 3
MAX_HAJM = 200_000  # belgi, bitta fayl uchun


# ---------- GitHub API ----------
def gh(yol, method="GET", data=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "restopulse-itchi",
        "Authorization": f"Bearer {GH_TOKEN}",
    }
    body = json.dumps(data).encode() if data is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"https://api.github.com{yol}", data=body, headers=headers, method=method
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode() or "{}")


class _RedirectYoq(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def log_yuklab_olish(run_id):
    """Run logini (zip) yuklab, yiqilgan qadamlarning oxirgi qismini qaytaradi."""
    # 1) Token bilan so'raymiz — GitHub imzolangan URL'ga yo'naltiradi
    opener = urllib.request.build_opener(_RedirectYoq)
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/logs",
        headers={"Authorization": f"Bearer {GH_TOKEN}", "User-Agent": "restopulse-itchi"},
    )
    try:
        opener.open(req, timeout=60)
        return ""  # redirect bo'lmadi — log yo'q
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302):
            print(f"! Log olishda xato: {e.code}", flush=True)
            return ""
        url = e.headers.get("Location", "")
    if not url:
        return ""
    # 2) Imzolangan URL'dan tokensiz yuklaymiz
    with urllib.request.urlopen(url, timeout=120) as r:
        zdata = r.read()
    matnlar = []
    with zipfile.ZipFile(io.BytesIO(zdata)) as z:
        for nom in z.namelist():
            if not nom.endswith(".txt"):
                continue
            try:
                t = z.read(nom).decode("utf-8", "replace")
            except Exception:
                continue
            # xato belgilari bor fayllarni afzal ko'ramiz
            if re.search(r"(?i)error|traceback|failed|exit code [1-9]", t):
                matnlar.append(f"--- {nom} (oxiri) ---\n{t[-2500:]}")
    if not matnlar:  # xato topilmasa — eng katta logning oxiri
        with zipfile.ZipFile(io.BytesIO(zdata)) as z:
            nomlar = sorted(z.namelist(), key=lambda n: z.getinfo(n).file_size)
            if nomlar:
                t = z.read(nomlar[-1]).decode("utf-8", "replace")
                matnlar.append(f"--- {nomlar[-1]} (oxiri) ---\n{t[-2500:]}")
    return "\n\n".join(matnlar[:3])


def yiqilgan_run_top():
    if RUN_ID:
        return gh(f"/repos/{REPO}/actions/runs/{RUN_ID}")
    runs = gh(f"/repos/{REPO}/actions/runs?status=failure&per_page=10").get(
        "workflow_runs", []
    )
    for r in runs:
        if r.get("name") not in OZIMIZ:
            return r
    return None


# ---------- Kontekst yig'ish ----------
def fayl_oqish(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def kontekst_yig(run):
    """Workflow fayli + u chaqiradigan .py fayllar + xato logi."""
    bolaklar = []
    wf_yol = run.get("path", "")  # masalan .github/workflows/stop_sayt.yml
    wf_matn = fayl_oqish(wf_yol) or ""
    if wf_matn:
        bolaklar.append(f"=== WORKFLOW FAYLI: {wf_yol} ===\n{wf_matn}")
    # yml ichida chaqirilgan python fayllarni topamiz
    py_fayllar = sorted(set(re.findall(r"([\w./-]+\.py)", wf_matn)))
    for p in py_fayllar[:3]:
        t = fayl_oqish(p)
        if t:
            bolaklar.append(f"=== KOD FAYLI: {p} ===\n{t[:20000]}")
    log = log_yuklab_olish(run["id"])
    if log:
        bolaklar.append(f"=== XATO LOGI ===\n{log}")
    return "\n\n".join(bolaklar), py_fayllar


# ---------- Claude tashxis + tuzatish ----------
def claude_tuzat(run, kontekst):
    system = (
        "Sen RestoPulse ekotizimining AI IT mutaxassisisan. GitHub Actions workflow yiqildi. "
        "Quyida workflow fayli, u chaqiradigan kod va xato logi berilgan.\n"
        "VAZIFA: xatoni tashxisla. Agar KOD faylini o'zgartirish bilan tuzatish mumkin bo'lsa — "
        "tuzatilgan faylning TO'LIQ yangi mazmunini ber.\n"
        "QAT'IY QOIDALAR:\n"
        "- Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"tashxis": "1-3 jumla, o\'zbekcha", "tuzatish_mumkinmi": true/false, '
        '"fayllar": [{"yol": "fayl.py", "mazmun": "to\'liq yangi mazmun"}], '
        '"izoh": "nima o\'zgartirilgani, 1-2 jumla", "maslahat": "tuzatib bo\'lmasa nima qilish kerak"}\n'
        "- .enc.json, .github/workflows/ ichidagi fayllar va shifr.py'ni O'ZGARTIRMA. "
        "Muammo workflow faylida bo'lsa: tuzatish_mumkinmi=false qil va maslahat'da "
        "workflow'ning tuzatilgan qismini matn sifatida tushuntir.\n"
        "- Muammo sekret/sozlamada bo'lsa (masalan API kaliti eskirgan): tuzatish_mumkinmi=false, "
        "maslahat'da aniq qadamlar.\n"
        "- Ehtiyotkor bo'l: keng qayta yozish emas, minimal aniq tuzatish. Ishonchsiz bo'lsang "
        "tuzatish_mumkinmi=false de — noto'g'ri tuzatishdan yo'q tuzatish yaxshi.\n"
        "- Kod izohlari va xabarlar o'zbek tilida qolsin."
    )
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 16000,
            "system": system,
            "messages": [
                {
                    "role": "user",
                    "content": f"Yiqilgan workflow: {run.get('name')}\n\n{kontekst[:60000]}",
                }
            ],
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
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode())
    matn = "".join(b.get("text", "") for b in data.get("content", [])).strip()
    matn = re.sub(r"^```(json)?|```$", "", matn.strip(), flags=re.M).strip()
    return json.loads(matn)


# ---------- Xavfsizlik filtri ----------
def fayl_ruxsatmi(yol):
    yol = yol.lstrip("./")
    if ".." in yol or yol.startswith("/"):
        return False
    if any(t in yol for t in TAQIQ_QISM):
        return False
    return yol.endswith(RUXSAT_KENGAYTMA)


# ---------- PR yaratish ----------
def sh(*args):
    subprocess.run(args, check=True)


def pr_och(run, natija):
    shox = f"itchi-tuzatish-{run['id']}"
    sh("git", "config", "user.name", "AI IT-chi")
    sh("git", "config", "user.email", "itchi@restopulse.local")
    sh("git", "checkout", "-b", shox)
    yozildi = []
    for f in natija.get("fayllar", [])[:MAX_FAYL]:
        yol, mazmun = f.get("yol", ""), f.get("mazmun", "")
        if not fayl_ruxsatmi(yol):
            print(f"! Taqiqlangan fayl o'tkazib yuborildi: {yol}", flush=True)
            continue
        if not mazmun or len(mazmun) > MAX_HAJM:
            continue
        with open(yol, "w", encoding="utf-8") as fp:
            fp.write(mazmun)
        sh("git", "add", yol)
        yozildi.append(yol)
    if not yozildi:
        return None, []
    sh("git", "commit", "-m", f"AI IT-chi tuzatishi: {run.get('name')}")
    sh("git", "push", "origin", shox)
    pr = gh(
        f"/repos/{REPO}/pulls",
        method="POST",
        data={
            "title": f"🤖 IT-chi tuzatishi: {run.get('name')}",
            "head": shox,
            "base": "main",
            "body": (
                f"**Tashxis:** {natija.get('tashxis', '')}\n\n"
                f"**Nima o'zgartirildi:** {natija.get('izoh', '')}\n\n"
                f"Yiqilgan run: {run.get('html_url', '')}\n\n"
                "⚠️ Bu AI taklifi — merge qilishdan oldin o'zgarishlarni ko'zdan kechiring. "
                "Merge = tasdiq, Close = rad."
            ),
        },
    )
    return pr.get("html_url"), yozildi


# ---------- Telegram ----------
def telegram(matn):
    data = urllib.parse.urlencode(
        {"chat_id": CHAT_ID, "text": matn[:4000], "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data=data
    )
    with urllib.request.urlopen(req, timeout=30):
        pass


# ---------- Asosiy oqim ----------
def main():
    run = yiqilgan_run_top()
    if not run:
        xabar = "🔧 IT-chi tuzatuvchi: hozircha yiqilgan workflow topilmadi — tuzatadigan narsa yo'q ✅"
        print(xabar, flush=True)
        telegram(xabar)
        return

    print(f"Yiqilgan run: {run.get('name')} (#{run.get('run_number')})", flush=True)
    kontekst, _ = kontekst_yig(run)
    if not kontekst.strip():
        telegram(
            f"🔧 IT-chi tuzatuvchi: '{run.get('name')}' yiqilgan, lekin kontekst yig'ib "
            f"bo'lmadi. Run: {run.get('html_url', '')}"
        )
        return

    try:
        natija = claude_tuzat(run, kontekst)
    except Exception as e:
        print(f"! Tashxis xatosi: {e}", flush=True)
        telegram(
            f"🔧 IT-chi tuzatuvchi: '{run.get('name')}' uchun tashxis qilib bo'lmadi ({e}). "
            f"Run: {run.get('html_url', '')}"
        )
        return

    tashxis = natija.get("tashxis", "(tashxis yo'q)")
    if natija.get("tuzatish_mumkinmi") and natija.get("fayllar"):
        pr_url, yozildi = pr_och(run, natija)
        if pr_url:
            telegram(
                f"🔧 IT-chi tuzatuvchi\n\n"
                f"❌ Yiqilgan: {run.get('name')}\n"
                f"🩺 Tashxis: {tashxis}\n"
                f"✏️ O'zgartirilgan fayllar: {', '.join(yozildi)}\n\n"
                f"Tuzatish tayyor — ko'rib chiqing va tasdiqlang (Merge):\n{pr_url}\n\n"
                f"⚠️ Bu AI taklifi. Merge = qabul, Close = rad."
            )
            return
    # Tuzatib bo'lmadi — tashxis + maslahat
    maslahat = natija.get("maslahat") or "Claude bilan yangi suhbatda ko'rib chiqing."
    telegram(
        f"🔧 IT-chi tuzatuvchi\n\n"
        f"❌ Yiqilgan: {run.get('name')}\n"
        f"🩺 Tashxis: {tashxis}\n\n"
        f"Avtomatik tuzatib bo'lmadi. Maslahat:\n{maslahat}\n\n"
        f"Run: {run.get('html_url', '')}"
    )


if __name__ == "__main__":
    main()

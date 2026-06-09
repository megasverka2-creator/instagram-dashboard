#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Insights Collector
=============================
Uchta Instagram Business akkaunt uchun ma'lumot yig'adi va tarixga saqlaydi.
Har kuni avtomatik ishlashi mumkin (cron/scheduler orqali).

Foydalanish:
    python3 instagram_collector.py

Natija: instagram_data.json fayliga yangi o'lchov qo'shiladi.
Dashboard (instagram_dashboard.html) shu fayldan o'qiydi.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# ╔═══════════════════════════════════════════════════════════╗
# ║  SOZLAMALAR — FAQAT SHU 4 QATORNI TO'LDIRING                ║
# ╚═══════════════════════════════════════════════════════════╝
# DIQQAT: bu qiymatlarni hech kimga ko'rsatmang, internetga yuklamang.

# 1) Uzoq muddatli tokeningizni qo'shtirnoq ichiga yozing:
ACCESS_TOKEN = ""  # GitHub'da Secret (IG_ACCESS_TOKEN) dan keladi

# 2) Har bir restoran uchun Instagram Business Account ID'ni
#    qo'shtirnoq ichiga yozing (me/accounts javobidan olgan ID'lar):
ACCOUNTS = {
     "benison_uz": "17841455964894264",
    "dieto_uz":   "17841479699303953",
    "eddo_uz":    "17841461424798889",
}

# (Agar token environment o'zgaruvchisida bo'lsa, u avtomatik ishlatiladi)
ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", ACCESS_TOKEN)

API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_data.json")

# =============================================================
#  API yordamchi funksiyalari
# =============================================================

def api_get(path, params=None):
    """Graph API'ga GET so'rovi yuboradi."""
    if params is None:
        params = {}
    params["access_token"] = ACCESS_TOKEN
    url = f"{BASE_URL}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ! API xato ({e.code}): {body[:300]}")
        return None
    except Exception as e:
        print(f"  ! Ulanish xatosi: {e}")
        return None


def get_account_profile(ig_id):
    """Akkauntning asosiy profil ma'lumotlari: followers, media soni."""
    data = api_get(ig_id, {
        "fields": "username,followers_count,media_count"
    })
    return data or {}


def get_account_insights(ig_id):
    """Akkaunt darajasidagi insights: reach, profil ko'rishlari (oxirgi 7 kun)."""
    result = {}
    data = api_get(f"{ig_id}/insights", {
        "metric": "reach",
        "period": "day",
        "metric_type": "total_value",
    })
    if data and data.get("data"):
        for item in data["data"]:
            tv = item.get("total_value", {})
            result[item["name"]] = tv.get("value", 0)
    return result


def get_top_posts(ig_id, limit=10):
    """Oxirgi postlar va ularning engagement ko'rsatkichlari."""
    posts = []
    data = api_get(f"{ig_id}/media", {
        "fields": "id,caption,media_type,permalink,timestamp,"
                  "like_count,comments_count,"
                  "insights.metric(reach,saved,shares)",
        "limit": limit,
    })
    if not data or not data.get("data"):
        return posts

    for m in data["data"]:
        insights = {}
        if "insights" in m and m["insights"].get("data"):
            for ins in m["insights"]["data"]:
                vals = ins.get("values", [])
                if vals:
                    insights[ins["name"]] = vals[0].get("value", 0)

        likes = m.get("like_count", 0)
        comments = m.get("comments_count", 0)
        saved = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        reach = insights.get("reach", 0)

        caption = (m.get("caption") or "").strip().replace("\n", " ")
        if len(caption) > 80:
            caption = caption[:77] + "..."

        posts.append({
            "id": m.get("id"),
            "caption": caption or "(izohsiz)",
            "type": m.get("media_type"),
            "permalink": m.get("permalink"),
            "timestamp": m.get("timestamp"),
            "likes": likes,
            "comments": comments,
            "saved": saved,
            "shares": shares,
            "reach": reach,
            "engagement": likes + comments + saved + shares,
        })

    posts.sort(key=lambda p: p["engagement"], reverse=True)
    return posts


# =============================================================
#  Asosiy yig'ish jarayoni
# =============================================================

def collect():
    print(f"\n=== Instagram ma'lumot yig'ish: {datetime.now():%Y-%m-%d %H:%M} ===")

    if "BU_YERGA" in ACCESS_TOKEN or "ACCOUNT_ID" in str(ACCOUNTS):
        print("\n  XATO: Sozlamalar to'ldirilmagan!")
        print("  ACCESS_TOKEN va ACCOUNTS qiymatlarini to'ldiring (fayl boshida).")
        sys.exit(1)

    snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "accounts": {},
    }

    for name, ig_id in ACCOUNTS.items():
        print(f"\n  -> {name} ({ig_id})")
        profile = get_account_profile(ig_id)
        if not profile:
            print(f"     o'tkazib yuborildi (ma'lumot olinmadi)")
            continue

        insights = get_account_insights(ig_id)
        posts = get_top_posts(ig_id, limit=12)

        snapshot["accounts"][name] = {
            "username": profile.get("username", name),
            "followers": profile.get("followers_count", 0),
            "media_count": profile.get("media_count", 0),
            "reach_7d": insights.get("reach", 0),
            "posts": posts,
        }
        print(f"     followers: {profile.get('followers_count', 0)}, "
              f"postlar: {len(posts)}, reach(7d): {insights.get('reach', 0)}")

    # Tarixni yuklash va yangisini qo'shish
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    # Agar bugun allaqachon yig'ilgan bo'lsa — yangilaymiz (qayta yozamiz)
    today = snapshot["date"]
    history = [h for h in history if h.get("date") != today]
    history.append(snapshot)
    history.sort(key=lambda h: h.get("date", ""))

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"\n  Saqlandi: {DATA_FILE}")
    print(f"  Jami o'lchovlar (kunlar): {len(history)}")
    print("=== Tugadi ===\n")


if __name__ == "__main__":
    collect()

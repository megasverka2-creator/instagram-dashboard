#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Insights Collector (v2 — professional ko'rsatkichlar)
================================================================
Uchta Instagram Business akkaunt uchun batafsil ma'lumot yig'adi.
Har kuni avtomatik ishlashi mumkin (GitHub Actions / cron orqali).

Yangi (v2) ko'rsatkichlar:
  - profil ko'rishlari (profile_views)
  - akkaunt reach (kunlik)
  - engagement rate (faollik darajasi)
  - reach/follower nisbati
  - kontent turi bo'yicha tahlil (rasm/video/karusel)
  - saqlashlar, ulashishlar (post darajasida)
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
ACCESS_TOKEN = ""  # GitHub'da Secret (IG_ACCESS_TOKEN) dan keladi

ACCOUNTS = {
    "benison_uz": "17841455964894264",
    "dieto_uz":   "17841479699303953",
    "eddo_uz":    "17841461424798889",
}

ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", ACCESS_TOKEN)

API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_data.json")

# =============================================================
#  API yordamchi
# =============================================================
def api_get(path, params=None):
    if params is None:
        params = {}
    params["access_token"] = ACCESS_TOKEN
    url = f"{BASE_URL}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ! API xato ({e.code}): {body[:200]}")
        return None
    except Exception as e:
        print(f"  ! Ulanish xatosi: {e}")
        return None


def get_account_profile(ig_id):
    data = api_get(ig_id, {"fields": "username,followers_count,media_count"})
    return data or {}


def get_account_insights(ig_id):
    """Akkaunt darajasidagi insights: reach + profil ko'rishlari (oxirgi 7 kun)."""
    result = {"reach": 0, "profile_views": 0}
    # reach
    data = api_get(f"{ig_id}/insights", {
        "metric": "reach", "period": "day", "metric_type": "total_value",
    })
    if data and data.get("data"):
        for item in data["data"]:
            result[item["name"]] = item.get("total_value", {}).get("value", 0)
    # profile_views (ba'zan alohida so'rov kerak; xato bo'lsa 0 qoladi)
    pv = api_get(f"{ig_id}/insights", {
        "metric": "profile_views", "period": "day", "metric_type": "total_value",
    })
    if pv and pv.get("data"):
        for item in pv["data"]:
            result[item["name"]] = item.get("total_value", {}).get("value", 0)
    return result


def _breakdown_to_dict(data, metric_name):
    """API'ning breakdown javobini oddiy {nom: son} lug'atiga aylantiradi."""
    out = {}
    if not data or not data.get("data"):
        return out
    for item in data["data"]:
        if item.get("name") != metric_name:
            continue
        tv = item.get("total_value", {})
        breakdowns = tv.get("breakdowns", [])
        for bd in breakdowns:
            for res in bd.get("results", []):
                dims = res.get("dimension_values", [])
                key = " · ".join(str(d) for d in dims) if dims else "?"
                out[key] = res.get("value", 0)
    return out


def get_demographics(ig_id):
    """Followerlar demografiyasi: yosh+jins, shaharlar, davlatlar.
    Faqat 100+ followerli akkauntlarda ishlaydi. Xato bo'lsa bo'sh qaytaradi."""
    demo = {"age_gender": {}, "cities": {}, "countries": {}}

    # Yosh + jins
    ag = api_get(f"{ig_id}/insights", {
        "metric": "follower_demographics", "period": "lifetime",
        "timeframe": "this_month", "metric_type": "total_value",
        "breakdown": "age,gender",
    })
    demo["age_gender"] = _breakdown_to_dict(ag, "follower_demographics")

    # Shaharlar
    ct = api_get(f"{ig_id}/insights", {
        "metric": "follower_demographics", "period": "lifetime",
        "timeframe": "this_month", "metric_type": "total_value",
        "breakdown": "city",
    })
    cities = _breakdown_to_dict(ct, "follower_demographics")
    # Top 8 shahar
    demo["cities"] = dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:8])

    # Davlatlar
    co = api_get(f"{ig_id}/insights", {
        "metric": "follower_demographics", "period": "lifetime",
        "timeframe": "this_month", "metric_type": "total_value",
        "breakdown": "country",
    })
    countries = _breakdown_to_dict(co, "follower_demographics")
    demo["countries"] = dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:8])

    return demo


def get_posts(ig_id, limit=25):
    """Postlar va ularning to'liq ko'rsatkichlari."""
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
        ins = {}
        if "insights" in m and m["insights"].get("data"):
            for i in m["insights"]["data"]:
                vals = i.get("values", [])
                if vals:
                    ins[i["name"]] = vals[0].get("value", 0)

        likes = m.get("like_count", 0) or 0
        comments = m.get("comments_count", 0) or 0
        saved = ins.get("saved", 0)
        shares = ins.get("shares", 0)
        reach = ins.get("reach", 0)

        caption = (m.get("caption") or "").strip().replace("\n", " ")
        if len(caption) > 90:
            caption = caption[:87] + "..."

        engagement = likes + comments + saved + shares
        # post engagement rate = engagement / reach (reach bo'lsa)
        post_er = round(engagement / reach * 100, 1) if reach else 0

        posts.append({
            "id": m.get("id"),
            "caption": caption or "(izohsiz)",
            "type": m.get("media_type"),
            "permalink": m.get("permalink"),
            "timestamp": m.get("timestamp"),
            "likes": likes, "comments": comments, "saved": saved,
            "shares": shares, "reach": reach,
            "engagement": engagement, "post_er": post_er,
        })
    return posts


def analyze_posts(posts, followers):
    """Postlardan umumiy professional ko'rsatkichlarni hisoblaydi."""
    if not posts:
        return {
            "total_engagement": 0, "avg_engagement": 0, "engagement_rate": 0,
            "total_saved": 0, "total_shares": 0, "total_reach": 0,
            "avg_reach": 0, "reach_rate": 0,
            "by_type": {}, "top_posts": [],
        }

    n = len(posts)
    total_eng = sum(p["engagement"] for p in posts)
    total_saved = sum(p["saved"] for p in posts)
    total_shares = sum(p["shares"] for p in posts)
    total_reach = sum(p["reach"] for p in posts)
    avg_reach = round(total_reach / n)

    # Engagement rate = o'rtacha engagement / followers * 100
    avg_eng = round(total_eng / n)
    eng_rate = round(avg_eng / followers * 100, 2) if followers else 0
    # Reach rate = o'rtacha reach / followers * 100
    reach_rate = round(avg_reach / followers * 100, 1) if followers else 0

    # Kontent turi bo'yicha
    by_type = {}
    for p in posts:
        t = p["type"] or "OTHER"
        if t not in by_type:
            by_type[t] = {"count": 0, "engagement": 0, "reach": 0}
        by_type[t]["count"] += 1
        by_type[t]["engagement"] += p["engagement"]
        by_type[t]["reach"] += p["reach"]
    for t in by_type:
        c = by_type[t]["count"]
        by_type[t]["avg_engagement"] = round(by_type[t]["engagement"] / c)

    top = sorted(posts, key=lambda p: p["engagement"], reverse=True)[:10]

    return {
        "total_engagement": total_eng, "avg_engagement": avg_eng,
        "engagement_rate": eng_rate,
        "total_saved": total_saved, "total_shares": total_shares,
        "total_reach": total_reach, "avg_reach": avg_reach,
        "reach_rate": reach_rate,
        "by_type": by_type, "top_posts": top,
    }


# =============================================================
#  Asosiy jarayon
# =============================================================
def check_token_expiry():
    """Token qachon tugashini tekshiradi. Kun sonini qaytaradi (yoki None)."""
    try:
        data = api_get("debug_token", {"input_token": ACCESS_TOKEN})
        if data and data.get("data"):
            expires_at = data["data"].get("expires_at", 0)
            if expires_at == 0:
                return {"days_left": None, "expires_at": None, "never": True}
            exp_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            days_left = (exp_dt - now).days
            return {
                "days_left": days_left,
                "expires_at": exp_dt.strftime("%Y-%m-%d"),
                "never": False,
            }
    except Exception as e:
        print(f"  ! Token tekshirishda xato: {e}")
    return {"days_left": None, "expires_at": None, "never": False}


def collect():
    print(f"\n=== Instagram ma'lumot yig'ish (v2): {datetime.now():%Y-%m-%d %H:%M} ===")

    if not ACCESS_TOKEN or "ACCOUNT_ID" in str(ACCOUNTS):
        print("\n  XATO: ACCESS_TOKEN yoki ACCOUNTS to'ldirilmagan!")
        sys.exit(1)

    snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "token": check_token_expiry(),
        "accounts": {},
    }

    for name, ig_id in ACCOUNTS.items():
        print(f"\n  -> {name}")
        profile = get_account_profile(ig_id)
        if not profile:
            print("     o'tkazib yuborildi")
            continue

        followers = profile.get("followers_count", 0)
        insights = get_account_insights(ig_id)
        posts = get_posts(ig_id, limit=25)
        analysis = analyze_posts(posts, followers)
        demographics = get_demographics(ig_id)

        snapshot["accounts"][name] = {
            "username": profile.get("username", name),
            "followers": followers,
            "media_count": profile.get("media_count", 0),
            "reach_7d": insights.get("reach", 0),
            "profile_views_7d": insights.get("profile_views", 0),
            "engagement_rate": analysis["engagement_rate"],
            "avg_engagement": analysis["avg_engagement"],
            "reach_rate": analysis["reach_rate"],
            "avg_reach": analysis["avg_reach"],
            "total_saved": analysis["total_saved"],
            "total_shares": analysis["total_shares"],
            "by_type": analysis["by_type"],
            "demographics": demographics,
            "posts": analysis["top_posts"],
        }
        print(f"     followers: {followers}, ER: {analysis['engagement_rate']}%, "
              f"reach(7d): {insights.get('reach', 0)}, profil ko'rish: {insights.get('profile_views', 0)}")

    # Tarixni yuklash + yangisini qo'shish
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

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

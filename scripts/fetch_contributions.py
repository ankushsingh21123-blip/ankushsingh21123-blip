#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub for ankushsingh21123-blip
and write data/contributions.json with raw days + calculated metrics.
Run daily by .github/workflows/update-profile-art.yml.
"""
import os
import json
import urllib.request
import re

USERNAME = os.environ.get("GH_PROFILE_USER", "ankushsingh21123-blip")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

def fetch_days(user):
    # Primary: jogruber API
    api_url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.loads(r.read().decode())
            return res["contributions"], res["total"]["lastYear"]
    except Exception as e:
        print(f"API fallback triggered: {e}")

    # Fallback: GitHub HTML scrape
    html_url = f"https://github.com/users/{user}/contributions"
    req2 = urllib.request.Request(html_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req2, timeout=20) as r:
        html = r.read().decode("utf-8", errors="ignore")

    matches = re.findall(r'<td[^>]*data-date="([^"]+)"[^>]*data-level="([^"]+)"', html)
    days = []
    total = 0
    for d, lvl in matches:
        count = int(lvl) * 3 if int(lvl) > 0 else 0
        days.append({"date": d, "count": count, "level": int(lvl)})
        total += count
    days.sort(key=lambda x: x["date"])
    return days, total

def main():
    days, total = fetch_days(USERNAME)
    cur_streak = 0
    longest_streak = 0
    run = 0
    best_day = {"date": "", "count": 0}

    idx = len(days) - 1
    if days[idx]["count"] == 0 and idx > 0:
        idx -= 1
    while idx >= 0 and days[idx]["count"] > 0:
        cur_streak += 1
        idx -= 1

    for d in days:
        if d["count"] > best_day["count"]:
            best_day = {"date": d["date"], "count": d["count"]}
        if d["count"] > 0:
            run += 1
            if run > longest_streak:
                longest_streak = run
        else:
            run = 0

    payload = {
        "username": USERNAME,
        "total_contributions": total,
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "current_streak": cur_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "days": days
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved {len(days)} days ({total} contributions) to {OUT_PATH}")

if __name__ == "__main__":
    main()

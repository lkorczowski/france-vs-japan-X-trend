"""POC v2 France vs Japan on X.

Usage (Mac terminal):
    export X_BEARER_TOKEN="your token"
    python3 poc_x_war_v2.py

Three checks:
1. Baseline volume before the war (counts/all, 15 Sep to 15 Oct 2026).
2. Relevance audit: 100 most recent posts per side, full text saved.
3. Hall of fame: viral posts from the accounts seen in the screenshots.

Estimated cost: 0.02 + 1.00 + up to 0.40 = about 1.50 USD (rates read on 2026-10-26).
Standard library only. Errors on one step are reported and the run continues.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("X_BEARER_TOKEN")
if not TOKEN:
    sys.exit("Set X_BEARER_TOKEN first.")

API = "https://api.x.com/2"
FIELDS = "public_metrics,created_at,lang,author_id,conversation_id,referenced_tweets"

SIDES = {
    "FR": '(japonais OR japonaise OR japonaises OR japon) lang:fr -is:retweet',
    "JA": '(フランス OR フランス人) lang:ja -is:retweet',
}

# Accounts from the screenshots of 2026-10-26 (both sides and neutral)
HALL_OF_FAME = ["BWhey69", "keymee__", "PkMemez0", "E2LaCaf", "akio_56183",
                "4Ud1CCuftl19105", "AsianDawn4", "Penaltina"]


def get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}"


def slim(p):
    m = p.get("public_metrics", {})
    return {"id": p["id"], "created_at": p.get("created_at"),
            "is_reply": any(r["type"] == "replied_to" for r in p.get("referenced_tweets", [])),
            "likes": m.get("like_count", 0), "reposts": m.get("retweet_count", 0),
            "replies": m.get("reply_count", 0), "quotes": m.get("quote_count", 0),
            "views": m.get("impression_count", 0), "text": p["text"].replace("\n", " ")}


report = {"run_at": datetime.now(timezone.utc).isoformat(), "baseline": {}, "audit": {}, "hall_of_fame": {}}

# 1. Baseline
for side, q in SIDES.items():
    data, err = get("tweets/counts/all", {"query": q, "granularity": "day",
                                          "start_time": "2026-09-15T00:00:00Z",
                                          "end_time": "2026-10-15T00:00:00Z"})
    if err:
        report["baseline"][side] = {"error": err}
    else:
        days = [d["tweet_count"] for d in data.get("data", [])]
        report["baseline"][side] = {"days": len(days), "avg_per_day": round(sum(days) / max(len(days), 1)),
                                    "max_per_day": max(days) if days else 0}

# 2. Relevance audit
for side, q in SIDES.items():
    data, err = get("tweets/search/recent", {"query": q, "max_results": 100,
                                             "sort_order": "recency", "tweet.fields": FIELDS})
    report["audit"][side] = {"error": err} if err else [slim(p) for p in data.get("data", [])]

# 3. Hall of fame (posts since 2026-10-19, up to 10 per account)
for handle in HALL_OF_FAME:
    data, err = get("tweets/search/recent", {"query": f"from:{handle} -is:retweet", "max_results": 10,
                                             "start_time": "2026-10-19T00:00:00Z", "tweet.fields": FIELDS})
    if err:
        report["hall_of_fame"][handle] = {"error": err}
    else:
        posts = sorted([slim(p) for p in data.get("data", [])], key=lambda x: -x["likes"])
        report["hall_of_fame"][handle] = posts[:3]

with open("poc_snapshot_v2.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("Baseline:", json.dumps(report["baseline"], ensure_ascii=False))
print("Audit sizes:", {k: (len(v) if isinstance(v, list) else v) for k, v in report["audit"].items()})
print("Hall of fame:", {k: (len(v) if isinstance(v, list) else v) for k, v in report["hall_of_fame"].items()})
print("\nSaved poc_snapshot_v2.json. Send it in the chat.")

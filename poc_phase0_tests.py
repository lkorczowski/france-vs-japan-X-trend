"""Phase 0 follow-up: test a rewritten query, recompute its baseline, refresh the hall of fame.

Usage:
    X_BEARER_TOKEN=... python3 poc_phase0_tests.py
Reads at most 70 posts (50 test + 20 hall of fame). Estimated cost about 0.37 USD.
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
FIELDS = "public_metrics,created_at,lang,author_id,referenced_tweets"
PRICE_POST, PRICE_COUNTS_RECENT, PRICE_COUNTS_ALL = 0.005, 0.005, 0.010

QUERIES = {
    "JA_v2": "(フランス人 OR フランス語 OR おフランス OR (フランス (差別 OR レイシスト OR 日本人 OR ヘイト OR 黒人 OR 原爆 OR 自殺))) lang:ja -is:retweet",
}
HALL_OF_FAME = ["BWhey69", "keymee__", "PkMemez0", "E2LaCaf", "akio_56183",
                "4Ud1CCuftl19105", "AsianDawn4", "Penaltina"]

cost = 0.0


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
    return {"id": p["id"], "author_id": p.get("author_id"), "created_at": p.get("created_at"),
            "is_reply": any(r["type"] == "replied_to" for r in p.get("referenced_tweets", [])),
            "likes": m.get("like_count", 0), "reposts": m.get("retweet_count", 0),
            "views": m.get("impression_count", 0), "text": p["text"].replace("\n", " ")}


out = {"run_at": datetime.now(timezone.utc).isoformat()}

for name, q in QUERIES.items():
    res = {"query": q}
    data, err = get("tweets/counts/all", {"query": q, "granularity": "day",
                                          "start_time": "2026-09-15T00:00:00Z",
                                          "end_time": "2026-10-15T00:00:00Z"})
    cost += PRICE_COUNTS_ALL
    if err:
        res["baseline"] = {"error": err}
    else:
        days = [d["tweet_count"] for d in data.get("data", [])]
        res["baseline"] = {"days": len(days), "avg_per_day": round(sum(days) / max(len(days), 1))}
    data, err = get("tweets/counts/recent", {"query": q, "granularity": "day"})
    cost += PRICE_COUNTS_RECENT
    res["recent"] = {"error": err} if err else [
        {"day": d["start"][:10], "count": d["tweet_count"]} for d in data.get("data", [])]
    data, err = get("tweets/search/recent", {"query": q, "max_results": 50,
                                             "sort_order": "recency", "tweet.fields": FIELDS})
    if err:
        res["sample"] = {"error": err}
    else:
        res["sample"] = [slim(p) for p in data.get("data", [])]
        cost += PRICE_POST * len(res["sample"])
    out[name] = res

hof_q = "(" + " OR ".join(f"from:{h}" for h in HALL_OF_FAME) + ") -is:retweet"
data, err = get("tweets/search/recent", {"query": hof_q, "max_results": 20, "sort_order": "relevancy",
                                         "tweet.fields": FIELDS, "expansions": "author_id",
                                         "user.fields": "username"})
if err:
    out["hall_of_fame"] = {"error": err}
else:
    users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
    posts = [dict(slim(p), handle=users.get(p.get("author_id"))) for p in data.get("data", [])]
    cost += PRICE_POST * len(posts)
    out["hall_of_fame"] = sorted(posts, key=lambda x: -x["likes"])

out["estimated_cost_usd"] = round(cost, 3)
os.makedirs("audit", exist_ok=True)
with open("audit/phase0_tests.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

for name in QUERIES:
    r = out[name]
    print(name, "baseline:", r["baseline"], "| recent:", r["recent"],
          "| sample:", len(r["sample"]) if isinstance(r["sample"], list) else r["sample"])
hof = out["hall_of_fame"]
print("Hall of fame:", [(p["handle"], p["likes"], p["views"]) for p in hof] if isinstance(hof, list) else hof)
print("Estimated cost:", out["estimated_cost_usd"], "USD")

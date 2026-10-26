"""Daily collector for the French-speaking X vs Japanese-speaking X scoreboard.

Usage:
    X_BEARER_TOKEN=... python3 collector.py          # daily run
    SAMPLE_AUDIT=1 X_BEARER_TOKEN=... python3 collector.py   # also saves a 50-post sample per side (local only)

Standard library only. Queries, handles and limits live in config.json.
Writes docs/data/latest.json, docs/data/history.csv, docs/data/snapshots/YYYY-MM-DD.json,
docs/data/tracked_posts.json and docs/data/runs.csv. Post text is never written to docs/.
Any API error stops the run with exit code 1. No retries.
"""
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "docs", "data")
SNAPSHOTS = os.path.join(DATA, "snapshots")
API = "https://api.x.com/2"
FIELDS = "public_metrics,created_at,lang,author_id"

with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)
PRICES = CFG["prices_usd"]
LIMITS = CFG["limits"]
TRACK = CFG["tracking"]

TOKEN = os.environ.get("X_BEARER_TOKEN")
if not TOKEN:
    sys.exit("X_BEARER_TOKEN is not set.")

NOW = datetime.now(timezone.utc)
TODAY = NOW.date().isoformat()
spend = {"posts": 0, "requests": 0, "cost": 0.0}


def log(*args):
    print(*args, flush=True)


def get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API error on {path}: HTTP {e.code}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {path}: {e.reason}")


def counts(endpoint, query, **params):
    spend["requests"] += 1
    spend["cost"] += PRICES["counts_all" if endpoint == "all" else "counts_recent"]
    data = get(f"tweets/counts/{endpoint}", dict(query=query, granularity="day", **params))
    return data.get("data", [])


def can_read(n):
    return (spend["posts"] + n <= LIMITS["max_posts_per_run"]
            and spend["cost"] + n * PRICES["post_read"] <= LIMITS["max_cost_per_run_usd"])


def read_posts(path, params, parents=False):
    """Search or lookup. Returns posts with their author handle. Each returned post is billed.

    With parents=True, the posts they reply to or quote come back too (expansion). Replies cluster
    under viral posts, so the parents are how the hall of fame finds them. Counted as billed reads.
    """
    expansions = "author_id,referenced_tweets.id,referenced_tweets.id.author_id" if parents else "author_id"
    params = dict(params, **{"tweet.fields": FIELDS, "expansions": expansions, "user.fields": "username"})
    data = get(path, params)
    users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
    posts = data.get("data", []) + (data.get("includes", {}).get("tweets", []) if parents else [])
    spend["requests"] += 1
    spend["posts"] += len(posts)
    spend["cost"] += PRICES["post_read"] * len(posts)
    for p in posts:
        p["handle"] = users.get(p.get("author_id"))
    return posts


def search(query, n, sort="relevancy", parents=False):
    if not can_read(2 * n if parents else n):
        log(f"Skipped search ({n} posts would exceed the run cap): {query[:60]}")
        return []
    return read_posts("tweets/search/recent", {"query": query, "max_results": n, "sort_order": sort}, parents)


def lookup(ids):
    out = []
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        if not can_read(len(chunk)):
            sys.exit(f"Lookup of {len(chunk)} tracked posts would exceed the run cap. Lower max_tracked.")
        out += read_posts("tweets", {"ids": ",".join(chunk)})
    return out


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_blocklist():
    words, subs = [], []
    with open(os.path.join(DATA, "blocklist.txt"), encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if not w or w.startswith("#"):
                continue
            (words if re.match(r"^[\w\s'-]+$", w, re.ASCII) or re.match(r"^[a-zà-ÿ\s'-]+$", w) else subs).append(w)
    rx = re.compile(r"(?<!\w)(" + "|".join(re.escape(w) for w in words) + r")(?!\w)") if words else None
    return lambda text: bool(rx and rx.search(text.lower())) or any(s in text for s in subs)


def side_of(post):
    for side, s in CFG["sides"].items():
        if post.get("lang") == s["lang"]:
            return side
    return None


def metrics(p):
    m = p.get("public_metrics", {})
    return {"likes": m.get("like_count", 0), "reposts": m.get("retweet_count", 0),
            "views": m.get("impression_count", 0)}


def full_days(buckets):
    """Keep only buckets that cover a whole UTC day."""
    out = {}
    for b in buckets:
        start = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
        if start.hour == start.minute == 0 and end - start == timedelta(days=1):
            out[start.date().isoformat()] = b["tweet_count"]
    return out


# 1. Baseline (cached per query, counts/all only when a query changes)
baseline_path = os.path.join(DATA, "baseline.json")
baseline = load_json(baseline_path, {})
for side, s in CFG["sides"].items():
    if baseline.get(side, {}).get("query") != s["query"]:
        days = [b["tweet_count"] for b in counts("all", s["query"],
                                                 start_time=CFG["baseline"]["start"] + "T00:00:00Z",
                                                 end_time=CFG["baseline"]["end"] + "T00:00:00Z")]
        baseline[side] = {"query": s["query"], "start": CFG["baseline"]["start"], "end": CFG["baseline"]["end"],
                          "avg_per_day": round(sum(days) / max(len(days), 1))}

# 2. Daily volume, last 7 days, plus a one-time backfill back to war_start
volume = {}
history_path = os.path.join(DATA, "history.csv")
history = {}
if os.path.exists(history_path):
    with open(history_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            history[(row["date"], row["side"])] = row
for side, s in CFG["sides"].items():
    volume[side] = full_days(counts("recent", s["query"]))
    first = min(volume[side])
    have = {d for (d, sd) in history if sd == side}
    if CFG["war_start"] < first and CFG["war_start"] not in have:
        volume[side].update(full_days(counts("all", s["query"], start_time=CFG["war_start"] + "T00:00:00Z",
                                             end_time=first + "T00:00:00Z")))
day = max(set.intersection(*(set(v) for v in volume.values())))

# 3. Hall of fame: discovery, then refresh of tracked posts
blocked = load_blocklist()
tracked_path = os.path.join(DATA, "tracked_posts.json")
tracked = {t["id"]: t for t in load_json(tracked_path, [])}
# Pinned posts: one post URL or ID per line. Always tracked, never evicted.
pinned = set()
pinned_path = os.path.join(DATA, "pinned_posts.txt")
if os.path.exists(pinned_path):
    with open(pinned_path, encoding="utf-8") as f:
        for line in f:
            m = re.search(r"(\d{15,})\s*$", line.split("?")[0].strip()) if not line.startswith("#") else None
            if m:
                pinned.add(m.group(1))
# Refresh first: it is the part the scores need. Discovery then spends what is left of the run cap.
fresh = {p["id"]: p for p in lookup(sorted(set(tracked) | pinned))}
# Discovery: the most relevant quotes of each side, plus the posts they quote.
# Viral posts collect quotes, so the parents are where the hot posts are. (is:quote OR is:reply) returns HTTP 503.
candidates = list(fresh.values())
for side, s in CFG["sides"].items():
    candidates += search(f"{s['query']} is:quote", TRACK["discovery_per_side"], parents=True)
if TRACK.get("discovery_handles"):
    handles_q = "(" + " OR ".join(f"from:{h}" for h in CFG["hall_of_fame_handles"]) + ") -is:retweet"
    candidates += search(handles_q, TRACK["discovery_handles"])
for p in candidates:
    side = side_of(p)
    if not side or not p.get("handle") or blocked(p["text"]):
        tracked.pop(p["id"], None)
        fresh.pop(p["id"], None)
        continue
    fresh[p["id"]] = p
    if p["id"] not in tracked:
        tracked[p["id"]] = {"id": p["id"], "side": side, "handle": p["handle"],
                            "created_at": p.get("created_at"), "added": TODAY}
for i in [i for i in tracked if i not in fresh]:
    log(f"Tracked post {i} is gone (deleted, protected or blocklisted), dropped.")
    del tracked[i]
posts = {i: dict(side=t["side"], handle=fresh[i].get("handle") or t["handle"],
                created_at=fresh[i].get("created_at") or t.get("created_at"), **metrics(fresh[i]))
         for i, t in tracked.items()}
keep = set(pinned)
for side in CFG["sides"]:
    ranked = sorted((i for i in posts if posts[i]["side"] == side), key=lambda i: -posts[i]["views"])
    keep.update(ranked[:TRACK["max_tracked"] // len(CFG["sides"])])
tracked = {i: t for i, t in tracked.items() if i in keep}
posts = {i: p for i, p in posts.items() if i in keep}

# 4. Optional recency sample (local only, contains text)
if os.environ.get("SAMPLE_AUDIT") == "1":
    os.makedirs(os.path.join(ROOT, "audit"), exist_ok=True)
    sample = {side: [{"id": p["id"], "text": p["text"]} for p in search(s["query"], 50, sort="recency")]
              for side, s in CFG["sides"].items()}
    save_json(os.path.join(ROOT, "audit", f"sample_{TODAY}.json"), sample)
    log("Sample audit saved:", {k: len(v) for k, v in sample.items()})

# 5. Scores
prev_files = sorted(f for f in os.listdir(SNAPSHOTS) if f.endswith(".json") and f[:10] < TODAY)
prev = load_json(os.path.join(SNAPSHOTS, prev_files[-1]), None) if prev_files else None
if prev:
    window_h = round((NOW - datetime.fromisoformat(prev["run_at"])).total_seconds() / 3600, 1)
    fire_mode = "delta"
else:
    window_h, fire_mode = None, "total"
scores = {}
for side in CFG["sides"]:
    fire = 0
    for i, p in posts.items():
        if p["side"] != side:
            continue
        now_eng = p["likes"] + p["reposts"]
        if fire_mode == "total":
            fire += now_eng
        elif i in prev["posts"]:
            q = prev["posts"][i]
            fire += max(0, now_eng - q["likes"] - q["reposts"])
        else:
            created = tracked[i].get("created_at")
            if created and datetime.fromisoformat(created.replace("Z", "+00:00")) > NOW - timedelta(hours=window_h):
                fire += now_eng
    vol = volume[side][day]
    scores[side] = {"volume": vol, "heat": round(vol / max(baseline[side]["avg_per_day"], 1), 2), "firepower": fire}

score_winners = {}
for k in ("volume", "heat", "firepower"):
    best = max(scores[s][k] for s in scores)
    top = [s for s in scores if scores[s][k] == best]
    score_winners[k] = top[0] if len(top) == 1 else "Draw"
wins = {s: sum(1 for w in score_winners.values() if w == s) for s in scores}
winner = next((s for s, n in wins.items() if n >= 2), "Draw")

# 6. Write outputs
snapshot = {"run_at": NOW.isoformat(), "day": day, "volume": volume, "scores": scores,
            "posts": {i: {k: p[k] for k in ("side", "handle", "likes", "reposts", "views")} for i, p in posts.items()}}
save_json(os.path.join(SNAPSHOTS, f"{TODAY}.json"), snapshot)
save_json(tracked_path, sorted(tracked.values(), key=lambda t: t["id"]))
save_json(baseline_path, baseline)

for side in CFG["sides"]:
    for d, v in volume[side].items():
        row = history.get((d, side), {"date": d, "side": side, "likes_tracked": "", "views_tracked": ""})
        row["volume"] = v
        row["baseline_ratio"] = round(v / max(baseline[side]["avg_per_day"], 1), 2)
        if d == day:
            row["likes_tracked"] = sum(p["likes"] for p in posts.values() if p["side"] == side)
            row["views_tracked"] = sum(p["views"] for p in posts.values() if p["side"] == side)
        history[(d, side)] = row
cols = ["date", "side", "volume", "baseline_ratio", "likes_tracked", "views_tracked"]
with open(history_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for key in sorted(history):
        w.writerow(history[key])

latest = {
    "updated_at": NOW.isoformat(timespec="seconds"),
    "day": day,
    "title": CFG["title"],
    "winner": winner,
    "winner_label": CFG["sides"][winner]["label"] if winner != "Draw" else "Draw",
    "score_winners": score_winners,
    "firepower_mode": fire_mode,
    "firepower_window_hours": window_h,
    "war_start": CFG["war_start"],
    "sides": {side: {
        "label": s["label"],
        "query": s["query"],
        "baseline_avg": baseline[side]["avg_per_day"],
        **scores[side],
        "top_posts": [{"handle": posts[i]["handle"], "likes": posts[i]["likes"], "views": posts[i]["views"],
                       "url": f"https://x.com/{posts[i]['handle']}/status/{i}"}
                      for i in sorted((i for i in posts if posts[i]["side"] == side),
                                      key=lambda i: -posts[i]["views"])[:5]],
    } for side, s in CFG["sides"].items()},
    "feed": [{"side": posts[i]["side"], "handle": posts[i]["handle"], "likes": posts[i]["likes"],
              "views": posts[i]["views"], "created_at": posts[i]["created_at"],
              "url": f"https://x.com/{posts[i]['handle']}/status/{i}"}
             for i in sorted((i for i in posts if posts[i]["created_at"]),
                             key=lambda i: posts[i]["created_at"], reverse=True)[:20]],
    "run": {"posts_read": spend["posts"], "requests": spend["requests"], "estimated_cost_usd": round(spend["cost"], 3)},
}
save_json(os.path.join(DATA, "latest.json"), latest)

runs_path = os.path.join(DATA, "runs.csv")
new_file = not os.path.exists(runs_path)
with open(runs_path, "a", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    if new_file:
        w.writerow(["run_at", "posts_read", "requests", "estimated_cost_usd"])
    w.writerow([latest["updated_at"], spend["posts"], spend["requests"], round(spend["cost"], 3)])

log(f"Day scored: {day}. Winner: {latest['winner_label']}. Score winners: {score_winners}")
for side in scores:
    log(f"  {side}: {scores[side]} | tracked {sum(1 for p in posts.values() if p['side'] == side)}")
log(f"Run cost: {spend['posts']} posts, {spend['requests']} requests, about {spend['cost']:.3f} USD")

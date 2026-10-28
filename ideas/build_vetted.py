"""Build docs/data/vetted.json from the annotated corpus (docs/data/ideas.json).

on_topic: every post read and tagged in the corpus, with its concept. Insults are counted but never promoted
(hide: true keeps them out of the hall of fame and the feed). off_topic: posts read and rejected, kept across runs.
Usage: python3 ideas/build_vetted.py [--off ID "reason"]...
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(ROOT, "docs/data/vetted.json")
ideas = json.load(open(os.path.join(ROOT, "docs/data/ideas.json"), encoding="utf-8"))
old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
label = {c["id"]: c["label"] for c in ideas["concepts"]}
off = old.get("off_topic", {})
args = sys.argv[1:]
while args[:1] == ["--off"]:
    off[args[1]] = args[2]
    args = args[3:]
on = {u["id"]: {"concept": u["concept"], "label": label[u["concept"]], "side": u["side"],
                **({"hide": True} if u["register"] == "insult" or not u["url"] else {})}
      for u in ideas["units"] if u["id"].isdigit() and u["id"] not in off}
json.dump({"note": "Posts read and tagged by hand (on_topic) or rejected (off_topic). Built by ideas/build_vetted.py.",
           "on_topic": on, "off_topic": off}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"vetted: {len(on)} on topic, {len(off)} off topic")

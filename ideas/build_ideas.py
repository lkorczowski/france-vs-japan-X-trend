"""Build the idea map from the manual annotations. Local: reads private data, writes docs/data/ideas.json
with paraphrased ideas, handles, views and links only (no post text).

Steps: units -> sentence embeddings of each idea -> UMAP 2D (t-SNE for comparison) -> concept centroids
-> quote edges -> duels (ratio = child views / parent views) -> Elo of concepts on rebuttal duels
-> agreement between unsupervised clusters and the hand-induced concepts (ARI).
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import annotations as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(ROOT, "analysis/corpus.json"), encoding="utf-8"))
USERS = C["users"]

# Blocklist from the collector: a unit whose raw text matches is never linked.
src = open(os.path.join(ROOT, "collector.py"), encoding="utf-8").read()
ns = {"os": os, "re": re, "DATA": os.path.join(ROOT, "docs/data")}
exec(src[src.index("def load_blocklist"):src.index("def side_of")], ns)
blocked = ns["load_blocklist"]()


def text_of(t):
    return (t.get("note_tweet") or {}).get("text") or t.get("text", "")


units = {}


def add(uid, handle, views, likes, ann, raw="", parent=None, rel=None, linkable=True):
    community, side, concept, idea, register = ann[:5]
    units[uid] = dict(id=uid, handle=handle, views=int(views), likes=int(likes), community=community, side=side,
                      concept=concept, idea=idea, register=register, parent=parent, rel=rel,
                      url=(f"https://x.com/{handle}/status/{uid}" if linkable and register != "insult" and not blocked(raw)
                           and uid.isdigit() else None))


for uid, ann in A.SEEDS.items():
    t = C["posts"][uid]
    add(uid, USERS[t["author_id"]]["username"], t["public_metrics"]["impression_count"],
        t["public_metrics"]["like_count"], ann, text_of(t))
for uid, ann in A.EXTRA.items():
    t = C["includes_posts"].get(uid) or C["posts"].get(uid)
    handle = USERS.get(t["author_id"], {}).get("username") if t else {"2112536789575413866": "areskipv"}.get(uid, "unknown")
    add(uid, handle, ann[5], t["public_metrics"]["like_count"] if t else 0, ann, text_of(t) if t else "")
for uid, ann in A.ORIGINS.items():
    add(uid, "origin", ann[5], 0, ann, linkable=False)

for uid, ann in A.SEARCH.items():
    if uid in units:
        continue
    add(uid, ann[5], ann[6], ann[7], ann[:5])

qdir = os.path.join(ROOT, "analysis/quotes")
for parent, quotes in A.QUOTES.items():
    rows = {}
    with open(os.path.join(qdir, parent + ".tsv"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            rows[p[0]] = p
    for qid, ann in quotes.items():
        r = rows[qid]
        if qid in units:  # already a seed: just record the edge
            units[qid]["parent"], units[qid]["rel"] = parent, ann[5]
            continue
        add(qid, r[1], r[2], r[3], ann, r[5], parent=parent, rel=ann[5])
for child, (parent, rel) in A.API_EDGES.items():
    units[child]["parent"], units[child]["rel"] = parent, rel

U = list(units.values())
print("units:", len(U), "| linked:", sum(1 for u in U if u["url"]))

# Embeddings and 2D projections
import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
import umap
from sklearn.manifold import TSNE, MDS
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
E = model.encode([u["idea"] for u in U], normalize_embeddings=True, show_progress_bar=False)
labels_hand = [u["concept"] for u in U]
k = len(set(labels_hand))
auto = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(E)
ari = adjusted_rand_score(labels_hand, auto)
print(f"ARI (idea-only Ward clusters vs hand concepts): {ari:.2f}")
xy = umap.UMAP(n_neighbors=10, min_dist=0.35, metric="cosine", random_state=7).fit_transform(E)
ts = TSNE(n_components=2, perplexity=15, metric="cosine", init="pca", random_state=7).fit_transform(E)

# pyLDAvis-style intertopic map: concept centroids -> cosine distances -> metric MDS
cids = sorted(set(labels_hand))
cent = np.array([E[[i for i, u in enumerate(U) if u["concept"] == c]].mean(0) for c in cids])
cent = cent / np.linalg.norm(cent, axis=1, keepdims=True)
D = np.clip(1 - cent @ cent.T, 0, None)
mds = MDS(n_components=2, dissimilarity="precomputed", random_state=7, n_init=8).fit_transform(D)
mds = (mds - mds.min(0)) / (mds.max(0) - mds.min(0))
CPOS = {c: (float(a), float(b)) for c, (a, b) in zip(cids, mds)}
for u in U:
    u["x"], u["y"] = 0.0, 0.0

# Concepts
concepts = {}
for cid, label in A.CONCEPTS.items():
    us = [u for u in U if u["concept"] == cid]
    if not us:
        continue
    w = np.array([max(u["views"], 1) for u in us], dtype=float)
    sv, cv = Counter(), Counter()
    for u in us:
        sv[u["side"]] += u["views"]
        cv[u["community"]] += u["views"]
    top = sorted(us, key=lambda u: -u["views"])
    concepts[cid] = dict(id=cid, label=label, n=len(us), views=int(w.sum()),
                         x=round(CPOS[cid][0], 4), y=round(CPOS[cid][1], 4),
                         side_views=dict(sv), community_views=dict(cv),
                         lead_idea=next((u["idea"] for u in top if u["register"] != "insult"), top[0]["idea"]),
                         top=[dict(handle=u["handle"], views=u["views"], url=u["url"], idea=u["idea"], side=u["side"],
                                   community=u["community"]) for u in top if u["url"]][:4],
                         elo=1500.0, wins=0, losses=0)

# Edges and duels
edges = defaultdict(lambda: dict(views=0, n=0, rel=Counter()))
duels = []
for u in sorted(U, key=lambda u: u["id"]):
    p = units.get(u["parent"]) if u["parent"] else None
    if not p:
        continue
    e = edges[(p["concept"], u["concept"])]
    e["views"] += u["views"]
    e["n"] += 1
    e["rel"][u["rel"]] += 1
    if u["rel"] == "rebut" and p["views"] > 0:
        ratio = u["views"] / p["views"]
        duels.append(dict(parent=p["id"], child=u["id"], ratio=round(ratio, 3)))
        a, b = concepts[u["concept"]], concepts[p["concept"]]
        if a is not b:
            ea = 1 / (1 + 10 ** ((b["elo"] - a["elo"]) / 400))
            s = 1.0 if ratio > 1 else 0.0
            a["elo"] += 32 * (s - ea)
            b["elo"] -= 32 * (s - ea)
            (a if s else b)["wins"] += 1
            (b if s else a)["losses"] += 1

for c in concepts.values():
    c["elo"] = round(c["elo"])


def card(x):
    return dict(handle=x["handle"], views=x["views"], idea=x["idea"], side=x["side"], community=x["community"],
                concept=x["concept"], url=x["url"])


duel_cards = []
for d in duels:
    p, c = units[d["parent"]], units[d["child"]]
    if p["side"] == c["side"]:
        continue
    duel_cards.append(dict(ratio=d["ratio"], parent=card(p), child=card(c)))
best = {}
for dc in duel_cards:  # one duel per original post: its strongest answer
    k = dc["parent"]["handle"] + dc["parent"]["idea"]
    if k not in best or dc["child"]["views"] > best[k]["child"]["views"]:
        best[k] = dc
duel_cards = sorted(best.values(), key=lambda d: -(d["parent"]["views"] + d["child"]["views"]))

side_views, comm_views = Counter(), Counter()
for u in U:
    side_views[u["side"]] += u["views"]
    comm_views[u["community"]] += u["views"]
total = sum(comm_views.values())

out = dict(
    generated_at="2026-10-27",
    method=dict(units=len(U), seeds=len(A.SEEDS), searched=len(A.SEARCH), quotes=sum(len(v) for v in A.QUOTES.values()),
                concepts=len(concepts), ari_auto_vs_hand=round(float(ari), 2), ari_raw_text=0.10,  # eval_raw.py, 238 posts, multilingual mpnet
               first_post="2026-10-06", last_post="2026-10-26", embedding="all-mpnet-base-v2",
                projection="concept centroids, cosine distance, metric MDS (pyLDAvis style); UMAP and t-SNE of single ideas kept for comparison"),
    sides={k: int(v) for k, v in side_views.items()},
    communities={k: int(v) for k, v in comm_views.most_common()},
    third_party_share=round(sum(v for k, v in comm_views.items() if k not in ("FR", "JA")) / total, 3),
    concepts=sorted(concepts.values(), key=lambda c: -c["views"]),
    edges=[dict(source=s, target=t, views=e["views"], n=e["n"], rel=e["rel"].most_common(1)[0][0])
           for (s, t), e in edges.items()],
    duels=duel_cards[:10],
    units=[dict(id=u["id"], concept=u["concept"], side=u["side"], community=u["community"],
                views=u["views"], handle=u["handle"], url=u["url"], idea=u["idea"], register=u["register"],
                parent=u["parent"], rel=u["rel"]) for u in U],
)
json.dump(out, open(os.path.join(ROOT, "docs/data/ideas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(dict(tsne=[[round(float(a), 3), round(float(b), 3)] for a, b in ts], umap_idea_only=xy.round(3).tolist(),
               ids=[u["id"] for u in U], auto=auto.tolist()),
          open(os.path.join(ROOT, "analysis/projections.json"), "w"))

print("sides:", dict(side_views))
print("communities:", comm_views.most_common())
print("third-party share of views:", out["third_party_share"])
for c in out["concepts"]:
    print(f"{c['id']} {c['label']:<32} views {c['views']/1e6:6.1f}M n={c['n']:<3} elo {c['elo']} {c['wins']}-{c['losses']} sides {({k: round(v/1e6,1) for k, v in c['side_views'].items()})}")
print("duels:", len(duels), "cross-side shown:", len(duel_cards))

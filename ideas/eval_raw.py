import json, os, warnings, re
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score as ari
d = json.load(open("docs/data/ideas.json")); C = json.load(open("analysis/corpus.json"))
raw = {}
for t in list(C["posts"].values()) + list(C["includes_posts"].values()):
    raw[t["id"]] = (t.get("note_tweet") or {}).get("text") or t["text"]
for f in [("analysis/quotes/" + x) for x in os.listdir("analysis/quotes")] + [("analysis/thirdparty/" + x) for x in os.listdir("analysis/thirdparty")]:
    for line in open(f, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) > 5: raw.setdefault(p[0], re.sub(r"^\[[^\]]*\]\s*", "", p[5]))
U = [u for u in d["units"] if u["id"] in raw]
hand = [u["concept"] for u in U]; k = len(set(hand))
m = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
for label, texts in [("raw post text (multilingual)", [raw[u["id"]] for u in U]), ("annotated idea (multilingual)", [u["idea"] for u in U])]:
    E = m.encode(texts, normalize_embeddings=True)
    print(f"{label:<32} n={len(U)} Ward ARI {ari(hand, AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(E)):.2f}")

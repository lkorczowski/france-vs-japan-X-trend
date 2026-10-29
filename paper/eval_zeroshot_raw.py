import json, os, re, warnings, numpy as np
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
d = json.load(open("docs/data/ideas.json")); C = json.load(open("analysis/corpus.json"))
raw = {}
for t in list(C["posts"].values()) + list(C["includes_posts"].values()):
    raw[t["id"]] = (t.get("note_tweet") or {}).get("text") or t["text"]
for f in [("analysis/quotes/" + x) for x in os.listdir("analysis/quotes")] + [("analysis/thirdparty/" + x) for x in os.listdir("analysis/thirdparty")]:
    for line in open(f, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) > 5: raw.setdefault(p[0], re.sub(r"^\[[^\]]*\]\s*", "", p[5]))
lab = {c["id"]: c["label"] for c in d["concepts"] if c["id"].startswith("B")}; ids = list(lab)
U = [u for u in d["units"] if u["id"] in raw and u["concept"] in lab]; hand = [u["concept"] for u in U]
m = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
L = m.encode([lab[i] for i in ids], normalize_embeddings=True)
R=[u["register"] for u in U]
for name, texts in [("raw", [raw[u["id"]] for u in U]), ("idea", [u["idea"] for u in U])]:
    S = m.encode(texts, normalize_embeddings=True) @ L.T
    t3 = np.argsort(-S, 1)[:, :3]
    ok = [ids[j] == h for j, h in zip(S.argmax(1), hand)]
    for r in ("humor","argument"): print(name, r, sum(1 for x in R if x==r), round(np.mean([o for o,x in zip(ok,R) if x==r]),3))

import json, warnings, numpy as np, collections as C
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
d = json.load(open("docs/data/ideas.json"))
U = [u for u in d["units"] if u["concept"].startswith("B")]
lab = {c["id"]: c["label"] for c in d["concepts"] if c["id"].startswith("B")}
ids = list(lab); hand = [u["concept"] for u in U]
maj = C.Counter(hand).most_common(1)[0][1] / len(U)
print("n", len(U), "beliefs", len(ids), "majority baseline", round(maj, 3))
for name in ["sentence-transformers/all-mpnet-base-v2", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"]:
    m = SentenceTransformer(name)
    E = m.encode([u["idea"] for u in U], normalize_embeddings=True)
    L = m.encode([lab[i] for i in ids], normalize_embeddings=True)
    S = E @ L.T
    p1 = [ids[j] for j in S.argmax(1)]
    top3 = np.argsort(-S, 1)[:, :3]
    a1 = np.mean([p == h for p, h in zip(p1, hand)])
    a3 = np.mean([h in [ids[j] for j in t] for t, h in zip(top3, hand)])
    print(name.split("/")[1], "zero-shot label top1", round(a1, 3), "top3", round(a3, 3))

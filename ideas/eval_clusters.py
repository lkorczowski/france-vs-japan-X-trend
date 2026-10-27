import json, sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "analysis")
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score as ari
d = json.load(open("docs/data/ideas.json"))
U = d["units"]; hand = [u["concept"] for u in U]; k = len(set(hand))
for name in ["sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/all-mpnet-base-v2"]:
    m = SentenceTransformer(name)
    E = m.encode([u["idea"] for u in U], normalize_embeddings=True)
    km = np.mean([ari(hand, KMeans(k, n_init=10, random_state=s).fit_predict(E)) for s in range(5)])
    ag = ari(hand, AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(E))
    print(f"{name.split('/')[1]:<20} KMeans ARI {km:.2f} | Ward ARI {ag:.2f}")

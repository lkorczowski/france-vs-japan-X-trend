"""Figure 1 for the LaTeX preprint: views per belief by stance. Reads docs/data/ideas.json, writes paper/fig1.pdf."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "docs/data/ideas.json"), encoding="utf-8"))
C = sorted([c for c in d["concepts"] if c["rope"]], key=lambda c: c["views"])
COL = {"supports": "#C2410C", "attacks": "#1D4ED8", "neutral": "#9CA3AF"}
NAME = {"supports": "Supports the belief", "attacks": "Attacks the belief", "neutral": "Neutral"}
plt.rcParams.update({"font.family": "serif", "font.size": 8})
fig, ax = plt.subplots(figsize=(6.3, 4.4))
y = range(len(C))
left = [0] * len(C)
for k in ("supports", "attacks", "neutral"):
    v = [c["stance_views"].get(k, 0) / 1e6 for c in C]
    ax.barh(y, v, left=left, color=COL[k], label=NAME[k], height=0.72, edgecolor="white", linewidth=0.8)
    left = [a + b for a, b in zip(left, v)]
for i, c in enumerate(C):
    ax.text(left[i] + 0.6, i, f'{c["views"]/1e6:.1f}M', va="center", color="#444", fontsize=7)
ax.set_yticks(list(y))
ax.set_yticklabels([f'{c["label"]} ({c["owner"]})' for c in C])
ax.set_xlabel("Views (millions)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#ddd", linewidth=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "paper/fig1.pdf"))
print("fig1.pdf")

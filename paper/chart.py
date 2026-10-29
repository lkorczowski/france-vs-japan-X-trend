"""Figure 1 of the preprint: views per belief, split by stance. Reads docs/data/ideas.json, writes paper/fig1.svg."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "docs/data/ideas.json"), encoding="utf-8"))
C = sorted([c for c in d["concepts"] if c["rope"]], key=lambda c: -c["views"])
COL = {"supports": "#C2410C", "attacks": "#1D4ED8", "neutral": "#9CA3AF"}
W, L, top, bh, gap = 760, 300, 34, 16, 6
scale = (W - L - 60) / max(c["views"] for c in C)
h = top + len(C) * (bh + gap) + 30
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" font-family="Helvetica, Arial, sans-serif" font-size="11">']
x = L
for k, lab in (("supports", "Supports the belief"), ("attacks", "Attacks the belief"), ("neutral", "Neutral")):
    s.append(f'<rect x="{x}" y="8" width="10" height="10" rx="2" fill="{COL[k]}"/><text x="{x+14}" y="17" fill="#111">{lab}</text>')
    x += 150
for i, c in enumerate(C):
    y = top + i * (bh + gap)
    s.append(f'<text x="{L-8}" y="{y+12}" text-anchor="end" fill="#111">{c["label"].replace("&","&amp;").replace(chr(39),"&#39;")} ({c["owner"]})</text>')
    x = L
    for k in ("supports", "attacks", "neutral"):
        v = c["stance_views"].get(k, 0)
        if v:
            w = v * scale
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w-2,1):.1f}" height="{bh}" rx="2" fill="{COL[k]}"/>')
            x += w
    s.append(f'<text x="{x+4:.1f}" y="{y+12}" fill="#444">{c["views"]/1e6:.1f}M</text>')
s.append(f'<line x1="{L}" y1="{top-4}" x2="{L}" y2="{h-26}" stroke="#999" stroke-width="1"/>')
s.append(f'<text x="{L}" y="{h-8}" fill="#444">Views in millions. Owner camp in brackets. No-belief bins excluded.</text></svg>')
open(os.path.join(ROOT, "paper/fig1.svg"), "w", encoding="utf-8").write("\n".join(s))
print("fig1.svg", len(C), "beliefs")

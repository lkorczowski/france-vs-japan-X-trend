# Phase 0 gate report

Run on 2026-10-26, 22:20 to 22:40 UTC. Result: **PASS**.

## Final queries

- French-speaking X: `(japonais OR japonaise OR japonaises OR japon) lang:fr -is:retweet` (unchanged)
- Japanese-speaking X: `(フランス人 OR フランス語 OR おフランス OR (フランス (差別 OR レイシスト OR 日本人 OR ヘイト OR 黒人 OR 原爆 OR 自殺))) lang:ja -is:retweet` (rewritten)

## Criterion 1 · WAR share of 60 % or more on both sides

| Side | Query | Sample | WAR | Share |
|---|---|---|---|---|
| FR | v1 | 97 most recent | 77 | 79 % |
| JA | v1 `(フランス OR フランス人)` | 99 most recent | 53 | 54 % |
| JA | v2 (final) | 49 most recent | 42 | 86 % |

WAR means the post takes part in or comments on the French-speaking vs Japanese-speaking clash (insults, stereotype memes, defence, calls for peace). NOISE means food, travel, news, general politics, products, language learning.
JA v1 noise was mostly news, French politics and products. JA v2 keeps posts that name French people or the French language, or pair France with a conflict word.
Caveat: 38 of the 49 v2 posts were also in the v1 sample (both pulled within minutes). On the v1 sample, the v2 filter kept 38 posts at 87 % WAR, which matches.
Labels: audit/labels_v1.json. Raw posts: poc_snapshot_v2.json and audit/phase0_tests.json (local only, contain post text, never committed).

## Criterion 2 · War-period daily volume at least 2 x baseline

Baseline: counts/all, 2026-09-15 to 2026-10-15, daily average.

| Side | Baseline avg/day | War days | Lowest war day | Ratio (lowest) |
|---|---|---|---|---|
| FR | 1,734 | 20 to 25/10: 9,470 · 6,847 · 5,895 · 8,335 · 10,456 · 11,226 | 5,895 | 3.4 x |
| JA v2 | 1,565 | 20 to 26/10: 14,558 · 12,018 · 7,605 · 8,454 · 9,460 · 8,588 · 7,457 | 7,457 | 4.8 x |

counts/all works on this account. 26/10 for JA is a partial day.

## Criterion 3 · Hall of fame returns at least 5 posts with like and view counts

The per-handle searches in poc_x_war_v2.py failed (HTTP 400: start_time 2026-10-19T00:00Z is outside the 7-day window). Replaced by one grouped query, `(from:BWhey69 OR ... OR from:Penaltina) -is:retweet`, relevancy, 20 posts.
Returned 20 posts with likes and views. Top: E2LaCaf 515 likes / 5,442 views, E2LaCaf 198 / 5,097, AsianDawn4 33 / 1,282, BWhey69 29 / 513.
Note: none of the screenshot accounts has a post at 1,000 likes or more in the last 7 days. The collector will also discover top posts from the side queries.

## Money spent

| Step | Units | Cost (USD) |
|---|---|---|
| counts/all x 2 (v1 baseline) | 2 requests | 0.02 |
| Relevance audit v1 | 196 posts | 0.98 |
| Hall of fame per-handle (HTTP 400, not billed) | 0 | 0.00 |
| counts/all + counts/recent (JA v2) | 2 requests | 0.015 |
| JA v2 test sample | 49 posts | 0.245 |
| Hall of fame grouped | 20 posts | 0.10 |
| **Total phase 0** | | **1.36** |

Estimates from the rates read on docs.x.com on 2026-10-26. Check the X console billing page for the billed figure.

## Spend so far (after phases 1 to 3)

| Step | Posts | Cost (USD) |
|---|---|---|
| Phase 0 | 265 | 1.36 |
| Collector, local run 1 | 30 | 0.18 |
| Collector, local run 2 (parent-post discovery) | 85 | 0.435 |
| Collector, first GitHub Action run, 2026-10-26 22:42 UTC | 77 | 0.395 |
| **Total** | | **2.37** |

Next runs: about 0.30 to 0.45 USD per day, logged in docs/data/runs.csv.

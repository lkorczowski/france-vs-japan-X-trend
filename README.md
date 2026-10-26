# French-speaking X vs Japanese-speaking X

A daily scoreboard of the clash between French-speaking and Japanese-speaking X.
Live page: https://lkorczowski.github.io/france-vs-japan-X-trend/

Every morning a GitHub Action reads the X API, scores both sides and updates the page.
Sides are the language of the post, not the nationality of the author.
The page never shows post text. It shows numbers, handles and links.

## How the score works

Three scores per side, for the last full UTC day:

- **Volume**: posts matching the side's query.
- **Heat**: volume divided by the daily average from 15 Sep to 15 Oct 2026, before the clash.
- **Firepower**: likes and reposts gained by tracked posts since the previous run.

Think of it as a tug of war on three ropes. The side that wins 2 of the 3 ropes wins the day. Otherwise it is a draw.

Tracked posts are found through quotes: each run pulls the most relevant quote posts of each side and the posts they quote. Viral posts collect quotes, so this is where the hot posts are. The 15 most viewed posts per side are kept. Posts listed in `docs/data/pinned_posts.txt` are always tracked. Any post whose text matches `docs/data/blocklist.txt` is never tracked.

## Files

| Path | What it is |
|---|---|
| `config.json` | Queries, labels, tracked accounts, limits, prices. The only file to edit for another topic. |
| `collector.py` | Daily run. Python standard library only. |
| `docs/index.html` | The page. No build step. Served by GitHub Pages from `/docs`. |
| `docs/data/latest.json` | Today's scores and top posts. Read by the page. |
| `docs/data/history.csv` | One row per day and side: date, side, volume, baseline_ratio, likes_tracked, views_tracked. |
| `docs/data/snapshots/` | One file per run day, used for the firepower delta. |
| `docs/data/pinned_posts.txt` | Post URLs always tracked. |
| `docs/data/runs.csv` | Posts read and estimated cost of every run. |
| `GATE-REPORT.md` | Phase 0 audit: query relevance, baseline, money spent. |

Data lives under `docs/data/` so GitHub Pages can serve it next to the page.

## Cost

X API pay-per-use, rates read on docs.x.com on 2026-10-26: 0.005 USD per post read, 0.005 USD per counts/recent request, 0.010 USD per counts/all request.

A daily run reads at most about 95 posts: 2 count requests, a refresh of up to 30 tracked posts plus pinned ones, then 2 quote searches with their quoted posts.
Expect about 0.30 to 0.45 USD per day. The code enforces two hard caps per run, set in `config.json`: 150 posts and 0.50 USD. Each run logs its estimated cost in `docs/data/runs.csv`.

## Set the secret

The X Bearer Token is read from the `X_BEARER_TOKEN` environment variable. It is never printed, logged or committed.

```bash
gh secret set X_BEARER_TOKEN --repo lkorczowski/france-vs-japan-X-trend
```

Run locally:

```bash
X_BEARER_TOKEN=... python3 collector.py
```

The Action runs every day at 06:37 UTC (about 07:37 Paris in winter). Start it by hand from the Actions tab, or:

```bash
gh workflow run daily.yml --repo lkorczowski/france-vs-japan-X-trend
```

If the API returns an error, the run stops and turns red. It never retries.

## Fork it for another topic

1. Fork the repo and set your own `X_BEARER_TOKEN` secret.
2. Edit `config.json`: `title`, `war_start`, the `baseline` window (a calm month before the event), and for each side its `label`, `lang` and `query`. Replace `hall_of_fame_handles` with accounts central to your topic.
3. Delete everything in `docs/data/` except `blocklist.txt`. The first run fetches the new baseline and backfills volume since `war_start`.
4. Enable GitHub Pages on the `main` branch, `/docs` folder. Run the workflow once.

Check your queries first. Pull 50 recent posts per side, label each one as on topic or noise, and aim for 60 % on topic or more. `GATE-REPORT.md` shows how this one was checked.

## License

MIT

# LILA BLACK — Player Journey Visualization

**Live URL:** https://final-submission-player-journey-vis.vercel.app/

Interactive browser-based tool for LILA Games level designers to explore player movement, events, and behavioral patterns across 5 days of LILA BLACK telemetry data.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Vanilla HTML + Canvas API | Zero dependencies, zero build step. Max ~800 events per match — Canvas is sufficient |
| Data pipeline | Python · pyarrow · pandas | Reliable parquet parsing; pre-processes 7.98 MB of raw data to static JSON offline |
| Hosting | Vercel (static) | Dataset fits in static files — no backend needed, instant deploys, free tier |

---

## Features

- **3 maps** — Ambrose Valley, Grand Rift, Lockdown — each with minimap overlay
- **Marker rendering** — distinct shapes and colours per event type (positions, kills, deaths, loot, storm deaths)
- **Human vs bot** toggle — see each population independently
- **Per-event-type filters** — isolate kills, deaths, loot, or storm deaths
- **Pan and zoom** — mouse drag + scroll wheel on the viewport
- **Hover tooltips** — event type, player ID, world coordinates
- **Match stats** — duration, event count, human/bot breakdown

---

## Repository Structure

```
lila-player-visualization/
├── public/                          # Everything Vercel serves
│   ├── index.html                   # The entire frontend (single file)
│   ├── minimaps/                    # Minimap images
│   │   ├── AmbroseValley_Minimap.png
│   │   ├── GrandRift_Minimap.png
│   │   └── Lockdown_Minimap.jpg
│   └── data/                        # Pre-processed match JSON
│       ├── map_AmbroseValley/
│       │   ├── index.json           # Match list for dropdown
│       │   └── match_*.json         # Per-match event data (566 files)
│       ├── map_GrandRift/
│       │   ├── index.json
│       │   └── match_*.json         # (59 files)
│       └── map_Lockdown/
│           ├── index.json
│           └── match_*.json         # (171 files)
├── scripts/
│   ├── export_to_json.py            # Parquet → JSON pre-processor
│   └── generate_match_index.py      # Builds index.json per map folder
├── data/                            # Raw .nakama-0 files (not committed)
│   └── player_data/
│       ├── February_10/ … February_14/
│       └── minimaps/
├── ARCHITECTURE.md
├── INSIGHTS.md
├── README.md
└── requirements.txt
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- A way to serve static files locally (Python's built-in server works fine)

### 1. Install Python dependencies
```bash
pip install pyarrow pandas Pillow
```

### 2. Place raw data
Put the unzipped `player_data/` folder at the repo root so the path is:
```
lila-player-visualization/data/player_data/February_10/...
```

### 3. Run the data pipeline
```bash
python scripts/export_to_json.py
```
This reads all `.nakama-0` files and writes per-match JSON to `public/data/`. Takes ~30 seconds for the full dataset.

```bash
python scripts/generate_match_index.py
```
This creates `index.json` inside each `public/data/map_*/` folder (needed for the match dropdown).

### 4. Serve locally
```bash
cd public
python -m http.server 8080
```
Open `http://localhost:8080` in Chrome.

> **Note:** Opening `index.html` directly as a `file://` URL will fail due to CORS restrictions on `fetch()`. Always use a local server.

---

## Environment Variables

None required. This is a fully static app — all data is pre-baked into JSON files at build time.

---

## Deployment (Vercel)

The `public/` directory is the Vercel root. Set the following in `vercel.json` (already included in repo):

```json
{
  "outputDirectory": "public"
}
```

Push to GitHub → Vercel auto-deploys on every push to `main`.

> **Critical:** The `minimaps/` folder must be inside `public/minimaps/` — not at the repo root. Vercel only serves what is inside the output directory.

---

## Using the Tool

1. **Select a map** from the dropdown — minimap loads automatically
2. **Select a match** from the second dropdown (populated per map)
3. Click **Load Match** — events render as markers on the minimap
4. **Toggle filters** (Humans/Bots, event types) to isolate what you need
5. **Pan** by clicking and dragging the viewport
6. **Zoom** with the scroll wheel
7. **Hover** over any non-position marker for a tooltip with event details

### Event marker legend

| Marker | Event |
|--------|-------|
| 🔵 Blue circle | Human position |
| 🟡 Yellow circle | Bot position |
| 🟢 Green diamond | Kill (BotKill or Kill) |
| 🔴 Red square | Death (BotKilled or Killed) |
| 🟣 Purple triangle | Storm death (KilledByStorm) |
| 🔷 Cyan diamond | Loot pickup |

---

## Data Pipeline Details

**Input:** `.nakama-0` files (Apache Parquet despite the extension)
**Filename format:** `{player_id}_{match_id}.nakama-0`

**Key data facts confirmed during exploration:**
- `ts` column type is `timestamp[ms]` in Parquet schema but raw int64 values are Unix seconds — treated as seconds throughout
- `event` column values are bytes — decoded as UTF-8
- Bot detection: numeric filename prefix = bot (e.g. `1441_...`), UUID prefix = human
- Coordinate axis used: `x` and `z` (not `y` — that is elevation, ignored)
- Minimap images are not 1024×1024: AmbroseValley=4320px, GrandRift=2160px, Lockdown=9000px

**Coordinate mapping:**
```python
u = (world_x - origin_x) / scale       # normalised [0, 1]
v = (world_z - origin_z) / scale       # normalised [0, 1]
pixel_x = u * canvas_width
pixel_y = (1 - v) * canvas_height      # Y flipped: game=bottom-left, image=top-left
```

---

## Dataset Summary

| Stat | Value |
|------|-------|
| Days of data | 5 (Feb 10–14, 2026) |
| Raw files | 1,243 |
| Unique matches | 796 |
| Human players | 245 |
| Bot IDs | 94 |
| Total events | 89,104 |
| Largest map (matches) | AmbroseValley — 566 matches |
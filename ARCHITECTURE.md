# ARCHITECTURE.md — LILA BLACK Player Journey Visualization

## What I Built and Why

A static single-page HTML/JS tool deployed on Vercel. The entire frontend is one `index.html` file using the Canvas API for rendering. No build step, no framework, no backend.

**Why this stack:**
- The full dataset is 7.98 MB of parquet that pre-processes to ~18 MB of JSON — well under Vercel's static hosting limits. A backend would add cost, latency, and deployment complexity with zero benefit at this data size.
- Canvas API handles 500–800 event markers per match with no perceptible lag. deck.gl or WebGL would be overengineering for this point count.
- Zero dependencies means zero version drift, zero npm install, and a URL that works immediately for any LILA reviewer without setup.

---

## Data Flow: Parquet → Screen

```
.nakama-0 files (1,243 files, 7.98 MB raw)
        │
        ▼
scripts/export_to_json.py  (Python, pyarrow + pandas)
  • Reads each file as Parquet
  • Decodes event column from bytes → UTF-8
  • Detects bots by filename prefix (numeric = bot, UUID = human)
  • Maps world (x, z) → UV [0–1] using per-map config from README
  • Computes match-relative timestamps (ts_raw - ts_min per match)
  • Outputs: public/data/map_{id}/{match_id}.json
             public/data/map_{id}/index.json  (match list for dropdown)
        │
        ▼
public/index.html  (browser)
  • Fetches index.json to populate match dropdown
  • On "Load Match": fetches match JSON, renders minimap PNG as <img>
  • Canvas draws event markers layered by type (positions → loot → kills/deaths)
  • Filters re-render instantly (no re-fetch)
  • Hover tooltip hit-tests against registered marker positions
```

---

## Coordinate Mapping — The Tricky Part

The game world uses a right-hand coordinate system with origin at a map-specific offset. The minimap images are NOT 1024×1024 (AmbroseValley = 4320px, GrandRift = 2160px, Lockdown = 9000px). I use a normalised UV approach that is image-size independent:

```
u = (world_x - origin_x) / scale        → [0, 1]
v = (world_z - origin_z) / scale        → [0, 1]

pixel_x = u × canvas_width
pixel_y = (1 − v) × canvas_height       ← Y axis is flipped:
                                            game origin = bottom-left
                                            image origin = top-left
```

**Per-map config** (from README, validated against data bounds):

| Map | origin_x | origin_z | scale |
|-----|----------|----------|-------|
| AmbroseValley | −370 | −473 | 900 |
| GrandRift | −290 | −290 | 581 |
| Lockdown | −500 | −500 | 1000 |

**Validation:** README provides example: world(−301.45, −355.55) on AmbroseValley → pixel(78, 890). Formula produces (78, 890). ✓ All three maps confirmed: 100% of event points fall within [0, 1] UV bounds.

**Key finding during exploration:** `ts` is stored as `timestamp[ms]` in Parquet schema but the raw int64 values are Unix seconds (not milliseconds). Treating them as ms gives 0.89s match durations; as seconds gives 13s–890s durations (median 6.4 min) which matches an extraction shooter. Match-relative time = `ts_raw − min(ts_raw)` per match.

---

## Assumptions

| Assumption | What I found / How I handled it |
|---|---|
| Bot detection field exists in data | No explicit field. Bot = filename prefix is numeric (e.g. `1441_`). Human = UUID prefix. Confirmed: 94 unique bot IDs, 245 human players. |
| Minimap images are 1024×1024 (per README) | Actual sizes: 4320, 2160, 9000px. Used UV normalisation so formula is image-size independent. |
| `ts` column is milliseconds (per Parquet schema) | Raw int64 values are Unix seconds stored in an ms-typed column. Extracted via `.astype('int64')`. |
| All maps have equal data coverage | AmbroseValley has 566 matches vs GrandRift's 59. Noted in README as expected (server population). |
| Human-vs-human PvP is common | Only 3 Kill + 3 Killed events across all 5 days. This is almost entirely a PvE dataset. |

---

## Tradeoffs

| Decision | Alternatives Considered | What I Chose | Why |
|---|---|---|---|
| Static JSON + Vercel | FastAPI backend, Streamlit Cloud | Static JSON | 7.98 MB parquet → 18 MB JSON fits in static hosting; no backend = simpler deploy, zero cold starts |
| Canvas API | deck.gl, Leaflet, Plotly | Canvas API | Max ~800 events per match — Canvas is sufficient and has zero bundle size |
| Pre-process all matches offline | On-demand parquet parsing in browser | Offline Python script | Apache Arrow in-browser is unstable; Python pyarrow is reliable and fast |
| Per-match JSON files | Single large JSON blob | Per-match files | Dropdown loads only the selected match (~5–40 KB) instead of 18 MB upfront |
| UV normalisation (0–1) | Hardcoded pixel dimensions | UV | Image-size independent; works even if minimap resolution changes |
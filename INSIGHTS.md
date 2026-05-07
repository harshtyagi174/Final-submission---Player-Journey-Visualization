# INSIGHTS.md — LILA BLACK Player Journey Analysis

**Data source:** 89,104 events across 796 matches · 5 days (Feb 10–14, 2026) · 245 human players · 94 bot IDs · 3 maps

---

## Insight 1: Storm Deaths Are Exclusively a Late-Game Problem — All 39 Happen in the Final Third of Matches

### What caught my eye
Filtering to `KilledByStorm` events and scrubbing the timeline, every single storm death sits in the final third of the match. Not one storm death occurs in the first two-thirds of any match across all 796 games.

### The evidence
Of the 39 total `KilledByStorm` events in the dataset, the match-phase breakdown is:

| Phase | Storm Deaths |
|-------|-------------|
| Early (0–33% of match time) | 0 |
| Mid (33–66% of match time) | 0 |
| Late (66–100% of match time) | **39 (100%)** |

Distribution across maps: AmbroseValley 17 · Lockdown 17 · GrandRift 5. The pattern holds identically on all three maps — this is not a map-specific quirk.

### What's actionable
The storm is functioning as a hard timer that catches slow-moving players at the very end of a match, not as a strategic pressure mechanic that influences decision-making throughout. A player can completely ignore the storm for two-thirds of the match and suffer no consequence.

**Metrics affected:**
- Storm death rate (currently 39 deaths across 796 matches = 0.049 per match — extremely low signal)
- Late-game survival rate and match duration distribution
- Player time-in-safe-zone across match phases

**Actionable items:**
1. Introduce a mid-game storm phase that begins at ~40% of match time at reduced damage — giving designers telemetry on whether players respond to earlier pressure without making it punishing
2. Add a `NearStorm` proximity event to the telemetry schema so future analysis can measure how long players spend in the danger zone before dying vs escaping
3. Compare storm death coordinates against loot-dense areas — if players are dying to storm in loot-rich zones, it suggests the loot placement is anchoring them past the safe window

### Why a level designer should care
Right now the storm has zero influence on player routing for 66% of match time. If the design intent is for the storm to shape mid-game rotations and create contested choke points, the telemetry shows it isn't working. The entire storm pressure compresses into the final minutes, which likely creates chaotic scrambles rather than strategic positioning decisions.

---

## Insight 2: Loot Is Almost Entirely a Human Activity — Bots Ignore 99.1% of Items

### What caught my eye
Toggling the Humans/Bots filter while viewing Loot events on any map, the loot markers almost completely disappear when humans are hidden. The spatial distribution of loot pickups changes dramatically between player types.

### The evidence
Of 12,885 total `Loot` events across the dataset:

| Player type | Loot events | Share |
|-------------|-------------|-------|
| Human | 12,770 | **99.1%** |
| Bot | 115 | 0.9% |

This is not proportional to event volume. Humans generate 74.3% of all events (66,161 rows) but 99.1% of loot pickups. Bots generate 25.7% of events (22,943 rows) but only 0.9% of loot. The ratio of loot per 1,000 position events: humans = 249, bots = 5.

Broken down by map, the pattern is consistent — bots never meaningfully engage with loot on any of the three maps.

### What's actionable
Bot pathing does not route through loot zones in any meaningful way. This creates two problems for level designers: (1) loot placement decisions can only be validated against human behaviour, making the dataset much smaller than it appears; (2) if bots are intended to create competitive pressure on loot — forcing players to move faster or contest items — they are failing to do that entirely.

**Metrics affected:**
- Loot competition rate (currently near-zero for bot vs human)
- Effective sample size for loot placement analysis (only 245 human players, not 339 total)
- Bot threat credibility in loot-dense areas

**Actionable items:**
1. Review bot AI waypoint graphs — they almost certainly do not include loot node types as objectives. Adding loot-seeking as a bot behaviour state would immediately create competitive tension
2. When analysing loot placement effectiveness, filter to human-only events. Bot loot data is noise
3. Track `LootContested` as a new event (two entities within X units of a loot point simultaneously) — this metric would capture whether the bot change creates real competition

### Why a level designer should care
Loot placement is one of the highest-leverage map design decisions in an extraction shooter — it drives routing, risk-taking, and early-game pacing. If bots don't contest loot, the designer gets no feedback on whether loot zones are correctly placed to create multi-party pressure. Every loot-placement decision is being evaluated only by human players, who make up less than three-quarters of the playerbase in this data window.

---

## Insight 3: Human Players Concentrate in the Lower-Left Quarter of AmbroseValley — Bots Use a Different Region Entirely

### What caught my eye
Viewing position events on AmbroseValley with humans and bots toggled separately, the heat patterns look noticeably different. Human positions cluster toward the lower-left of the minimap; bot positions are spread more evenly across the left half but avoid the lower-right quadrant that humans also avoid.

### The evidence
Position event distribution by map quadrant on AmbroseValley (largest map, 566 matches, 51,347 position events):

| Quadrant | Human % | Bot % | Difference |
|----------|---------|-------|------------|
| Lower-left (u<0.5, v<0.5) | **39.3%** | 41.5% | Similar |
| Upper-left (u<0.5, v>0.5) | **31.5%** | **42.4%** | Bots skew upper |
| Lower-right (u>0.5, v<0.5) | **18.8%** | 6.5% | Humans skew right |
| Upper-right (u>0.5, v>0.5) | 10.4% | 9.5% | Similar |

The right half of the map (u > 0.5) sees 29.2% of human positions but only 16% of bot positions. Bots are avoiding the right side of AmbroseValley at roughly half the rate of humans.

Cross-checking with `BotKill` events (humans killing bots): 1,797 of 2,415 total BotKills are on AmbroseValley, with kills concentrated in the left half — consistent with where bots actually are.

### What's actionable
Bots are routing away from approximately one-third of the AmbroseValley playable area. This means the right portion of the map generates almost no bot encounters for human players who venture there. A human who moves to the right side of AmbroseValley is effectively alone.

**Metrics affected:**
- Bot encounter rate by map zone (currently near-zero for right half of AmbroseValley)
- Player time spent in bot-sparse zones vs bot-dense zones
- Perceived difficulty distribution across the map

**Actionable items:**
1. Review AmbroseValley bot navigation mesh — there is likely a pathing obstacle or missing waypoint graph coverage on the right half of the map
2. Add bot spawn points or waypoints in the u>0.5 zone to balance encounter distribution
3. Use this as a template check for GrandRift and Lockdown — run the same quadrant analysis once more match data accumulates for those maps (GrandRift has only 59 matches in this window)

### Why a level designer should care
A map zone that bots never patrol is functionally a safe zone for experienced players who know about it. In an extraction shooter where tension comes from unpredictable encounters, a predictable safe corridor breaks the intended experience. This also means any loot placed on the right half of AmbroseValley is uncontested — undermining whatever risk/reward balance the designer intended for that area.
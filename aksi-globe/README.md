# AKSI Globe

Real-time 3D Earth simulation platform with AI-driven objects, AKSI metrics, Resonance Field, semantic event search, Memory_AKSI, and DIMAX v3 analytics panel.

## Features

### Core
- Interactive 3D Earth rendered with HTML5 Canvas
- Real-time object movement powered by Socket.IO WebSockets
- AI logic for spawning and moving objects with roles (scout / trader / cluster / signal)
- AKSI Index: **(A × I × S) × (1 + γ√n)** — attention, sincerity, agreement
- Live heatmap overlay showing activity hot zones
- Phase 3 history snapshots with summary API

### Resonance Field (эмоциональный резонанс)
- Formula: `Resonance = entropy × (AKSI / max_AKSI) × diversity_factor`
- **High resonance (> 0.7)** — objects get enhanced glow and cluster speed boost (+10%)
- **Low resonance (< 0.3)** — all objects slow down
- Visual aura around the globe changes color (red → blue) with resonance level
- Pulsing animation in the UI panel when resonance > 0.8

### Semantic Event Search (локальный, без внешних API)
- Bag-of-words vectors for each event (based on 15-keyword vocabulary)
- Cosine similarity search across the last 50 indexed events
- REST endpoint: `GET /api/search-events?query=...` → top-5 results
- Search UI panel at the bottom of the screen

### Memory_AKSI (BioMemory-style)
- Snapshots every 10 seconds: `{timestamp, aksi, resonance, objectsCount, topEvent, entropy, flow}`
- Circular buffer of 100 snapshots
- REST endpoint: `GET /api/memory` → all snapshots + summary stats
- **Replay button** in the UI — animates through memory snapshots step-by-step (0.5s/step)

### DIMAX v3 Panel
- Formula: `DIMAX = (D × I × √AX × 0.75 + M × 1.3 + Balance_bonus + SSB) / 3.5`
  - **D** (Depth) = resonance + entropy, normalized
  - **I** (Impact) = AKSI × objectsCount / 100
  - **AX** (Acceleration) = AKSI growth rate over last 30 seconds
  - **M** (Materialization) = 0.85 (static)
  - **Balance_bonus** = 0.08 × (1 − max_axis + min_axis)
  - **SSB** = 0.15 (static)
- Real-time breakdown panel in the lower-left corner

## Project Structure

```
aksi-globe/
├── backend/
│   ├── server.js          # Express + Socket.IO server
│   ├── ai.js              # AI object update logic (with resonance drift)
│   ├── aksi-core.js       # AKSI = (A×I×S) × (1+γ√n)
│   ├── resonance.js       # Resonance Field calculation
│   ├── semantic-search.js # Local cosine-similarity event search
│   ├── memory.js          # Memory_AKSI snapshot system
│   ├── metrics.js         # World metrics + DIMAX v3
│   ├── events.js          # Event generation
│   ├── history.js         # Phase 3 history snapshots
│   ├── heatmap.js         # Activity heatmap
│   ├── data-ingest.js     # External data adapters (OpenSky, AIS)
│   └── package.json
├── frontend/
│   ├── index.html         # Main HTML (all UI panels)
│   ├── main.js            # Socket.IO client + orchestration
│   ├── globe.js           # Canvas globe + resonance aura
│   ├── ui.js              # All panels: AKSI, Resonance, DIMAX, Memory, Search
│   └── style.css
├── shared/
│   └── config.json
└── docker-compose.yml
```

## Quick Start

```bash
cd aksi-globe/backend
npm install
npm start
```

Open http://localhost:3000

## Docker

```bash
docker-compose up -d
```

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/metrics` | Current metrics: stats, aksi, events, resonance, dimax |
| `GET /api/history?n=60` | Last N history snapshots |
| `GET /api/history/summary` | History summary (avgAksi, maxAksi, duration) |
| `GET /api/heatmap` | Active heatmap hotspots |
| `GET /api/memory` | Memory_AKSI snapshots + summary |
| `GET /api/search-events?query=...` | Semantic event search (cosine similarity) |

### Semantic Search Example

```bash
# Find events related to scout activity
curl "http://localhost:3000/api/search-events?query=scout+surge"

# Find clustering events
curl "http://localhost:3000/api/search-events?query=cluster+active"
```

Response:
```json
{
  "query": "scout surge",
  "results": [
    { "event": { "type": "scout_surge", "label": "Scout surge", "count": 7 }, "score": 0.894 },
    { "event": { "type": "swarm", "label": "Swarm detected", "strength": "0.70" }, "score": 0.45 }
  ]
}
```

## WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `init` | Server → Client | Initial objects array |
| `update` | Server → Client | `{ objects, stats, aksi, events, resonance, dimax, heatmap?, memoryUpdate? }` |
| `heatmap` | Server → Client | Hotspots array (on connect) |
| `history` | Server → Client | Last 60 history snapshots (on connect) |
| `memory` | Server → Client | Memory_AKSI snapshots (on connect) |

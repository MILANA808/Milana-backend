# AKSI Globe

Real-time 3D Earth visualization with AI-driven objects and metrics.

## Features

- Interactive 3D Earth rendered with HTML5 Canvas
- Real-time object movement powered by Socket.IO WebSockets
- AI logic for spawning and moving objects across the globe
- Live metrics panel (object count, average speed, density)
- Game-like UI with dark space theme

## Project Structure

```
aksi-globe/
├── backend/
│   ├── server.js      # Express + Socket.IO server
│   ├── ai.js          # AI object update logic
│   ├── metrics.js     # Metrics calculation
│   └── package.json   # Dependencies
├── frontend/
│   ├── index.html     # Main HTML page
│   ├── main.js        # Socket.IO client + orchestration
│   ├── globe.js       # Canvas globe rendering
│   ├── ui.js          # Metrics panel UI
│   └── style.css      # Dark space theme styles
├── shared/
│   └── config.json    # Shared configuration
└── docker-compose.yml # Docker deployment
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

## API (WebSocket Events)

| Event | Direction | Payload |
|-------|-----------|---------|
| `init` | Server → Client | Initial objects array |
| `update` | Server → Client | `{ objects, stats }` |

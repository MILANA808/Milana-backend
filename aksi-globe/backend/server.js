const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const path = require("path");
const metrics = require("./metrics");
const ai = require("./ai");
const aksiCore = require("./aksi-core");
const events = require("./events");
const history = require("./history");
const heatmap = require("./heatmap");
const resonance = require("./resonance");
const semanticSearch = require("./semantic-search");
const memory = require("./memory");

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(express.json());
app.use(express.static(path.join(__dirname, "../frontend")));

let objects = [];
let simulationInterval = null;
let tickCount = 0;
let lastResonance = { resonance: 0, level: "low" };

// Загружаем историю при старте
history.load();

// REST API — история (Phase 3)
app.get("/api/history", (req, res) => {
    const n = parseInt(req.query.n) || 60;
    res.json(history.getLast(n));
});

// REST API — сводка истории
app.get("/api/history/summary", (req, res) => {
    res.json(history.getSummary());
});

// REST API — тепловая карта
app.get("/api/heatmap", (req, res) => {
    const threshold = parseFloat(req.query.threshold) || 0.1;
    res.json(heatmap.getHotspots(threshold));
});

// REST API — текущие метрики
app.get("/api/metrics", (req, res) => {
    const stats = metrics.calc(objects);
    const aksi = aksiCore.calcAKSI(objects);
    const evts = events.generate(objects, aksi);
    const res_ = resonance.calcResonance(aksi);
    const dimax = metrics.calcDIMAX(stats, aksi, res_);
    const summary = history.getSummary();
    res.json({ stats, aksi, events: evts, resonance: res_, dimax, historySummary: summary });
});

// REST API — семантический поиск по событиям
app.get("/api/search-events", (req, res) => {
    const query = req.query.query || "";
    if (!query.trim()) {
        return res.status(400).json({ error: "query parameter is required" });
    }
    const results = semanticSearch.searchEvents(query);
    res.json({ query, results });
});

// REST API — Memory_AKSI
app.get("/api/memory", (req, res) => {
    res.json({
        snapshots: memory.getSnapshots(),
        summary: memory.getSummary()
    });
});

// Запускаем симуляцию один раз (не на каждое подключение)
function startSimulation() {
    if (simulationInterval) return;
    simulationInterval = setInterval(() => {
        tickCount++;

        objects = ai.update(objects, lastResonance.resonance);
        const stats = metrics.calc(objects);
        const aksi = aksiCore.calcAKSI(objects);
        const evts = events.generate(objects, aksi);

        // Индексируем события для семантического поиска
        evts.forEach(evt => semanticSearch.indexEvent(evt));

        // Рассчитываем Resonance Field
        const res = resonance.calcResonance(aksi);
        lastResonance = res;

        // Рассчитываем DIMAX v3
        const dimax = metrics.calcDIMAX(stats, aksi, res);

        // Обновляем тепловую карту
        heatmap.update(objects);

        // Записываем снимок в историю (Phase 3)
        history.record(stats, aksi, evts);

        // Записываем снимок в Memory_AKSI (каждые 10 тиков)
        memory.tick(stats, aksi, res, evts);

        // Каждые 60 тиков отправляем тепловую карту клиентам
        const hotspots = (tickCount % 60 === 0) ? heatmap.getHotspots(0.1) : null;

        // Каждые 10 тиков отправляем снапшоты памяти клиентам
        const memoryUpdate = (tickCount % 10 === 0) ? memory.getLast(20) : null;

        io.emit("update", {
            objects,
            stats,
            aksi,
            events: evts,
            resonance: res,
            dimax,
            heatmap: hotspots,
            memoryUpdate,
            tick: tickCount
        });
    }, 1000);
    console.log("Simulation started");
}

io.on("connection", (socket) => {
    console.log("user connected");

    // Отправляем текущее состояние новому клиенту
    socket.emit("init", objects);

    // Отправляем тепловую карту при подключении
    socket.emit("heatmap", heatmap.getHotspots(0.1));

    // Отправляем историю при подключении (последние 60 снимков)
    socket.emit("history", history.getLast(60));

    // Отправляем Memory_AKSI снапшоты при подключении
    socket.emit("memory", memory.getSnapshots());

    startSimulation();

    socket.on("disconnect", () => {
        console.log("user disconnected");
    });
});

// Сохраняем историю при завершении
process.on("SIGINT", () => {
    console.log("\nShutting down, saving history...");
    history.flush();
    process.exit(0);
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`AKSI Globe running on http://localhost:${PORT}`));

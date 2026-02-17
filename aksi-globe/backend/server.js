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

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(express.json());
app.use(express.static(path.join(__dirname, "../frontend")));

let objects = [];
let simulationInterval = null;
let tickCount = 0;

// Загружаем историю при старте
history.load();

// REST API — история
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
    const summary = history.getSummary();
    res.json({ stats, aksi, events: evts, historySummary: summary });
});

// Запускаем симуляцию один раз (не на каждое подключение)
function startSimulation() {
    if (simulationInterval) return;
    simulationInterval = setInterval(() => {
        tickCount++;

        objects = ai.update(objects);
        const stats = metrics.calc(objects);
        const aksi = aksiCore.calcAKSI(objects);
        const evts = events.generate(objects, aksi);

        // Обновляем тепловую карту
        heatmap.update(objects);

        // Записываем снимок в историю
        history.record(stats, aksi, evts);

        // Каждые 60 тиков отправляем тепловую карту клиентам
        const hotspots = (tickCount % 60 === 0) ? heatmap.getHotspots(0.1) : null;

        io.emit("update", {
            objects,
            stats,
            aksi,
            events: evts,
            heatmap: hotspots,
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

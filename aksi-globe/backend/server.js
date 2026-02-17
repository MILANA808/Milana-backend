const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const path = require("path");
const metrics = require("./metrics");
const ai = require("./ai");
const aksiCore = require("./aksi-core");
const events = require("./events");

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(express.static(path.join(__dirname, "../frontend")));

let objects = [];
let simulationInterval = null;

// Запускаем симуляцию один раз (не на каждое подключение)
function startSimulation() {
    if (simulationInterval) return;
    simulationInterval = setInterval(() => {
        objects = ai.update(objects);
        const stats = metrics.calc(objects);
        const aksi = aksiCore.calcAKSI(objects);
        const evts = events.generate(objects, aksi);
        io.emit("update", { objects, stats, aksi, events: evts });
    }, 1000);
    console.log("Simulation started");
}

io.on("connection", (socket) => {
    console.log("user connected");

    // Отправляем текущее состояние новому клиенту
    socket.emit("init", objects);

    startSimulation();

    socket.on("disconnect", () => {
        console.log("user disconnected");
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`AKSI Globe running on http://localhost:${PORT}`));

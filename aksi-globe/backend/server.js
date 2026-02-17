const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const path = require("path");
const metrics = require("./metrics");
const ai = require("./ai");

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

app.use(express.static(path.join(__dirname, "../frontend")));

let objects = [];

io.on("connection", (socket) => {
    console.log("user connected");

    socket.emit("init", objects);

    const interval = setInterval(() => {
        objects = ai.update(objects);
        const stats = metrics.calc(objects);
        io.emit("update", { objects, stats });
    }, 1000);

    socket.on("disconnect", () => {
        console.log("user disconnected");
        clearInterval(interval);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`AKSI Globe running on http://localhost:${PORT}`));

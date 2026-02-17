import { drawGlobe, updateObjects } from "./globe.js";
import { updateUI } from "./ui.js";

const socket = io();

socket.on("init", data => {
    drawGlobe();
    updateObjects(data);
});

socket.on("update", data => {
    updateObjects(data.objects);
    updateUI(data.stats, data.aksi, data.events);
});

// Перерисовываем глобус при изменении размера окна
window.addEventListener("resize", () => {
    drawGlobe();
});

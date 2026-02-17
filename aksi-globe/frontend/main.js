import { drawGlobe, updateObjects, updateHeatmap } from "./globe.js";
import { updateUI, updateHistory } from "./ui.js";

const socket = io();

socket.on("init", data => {
    drawGlobe();
    updateObjects(data);
});

socket.on("update", data => {
    updateObjects(data.objects);
    updateUI(data.stats, data.aksi, data.events);

    // Обновляем тепловую карту если пришла
    if (data.heatmap) {
        updateHeatmap(data.heatmap);
    }
});

// Тепловая карта при подключении
socket.on("heatmap", data => {
    updateHeatmap(data);
});

// История при подключении
socket.on("history", data => {
    updateHistory(data);
});

// Перерисовываем глобус при изменении размера окна
window.addEventListener("resize", () => {
    drawGlobe();
});

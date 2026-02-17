import { drawGlobe, updateObjects, updateHeatmap, setResonance } from "./globe.js";
import { updateUI, updateHistory, updateMemory, initReplayButton, initSemanticSearch } from "./ui.js";

const socket = io();

socket.on("init", data => {
    drawGlobe();
    updateObjects(data);
});

socket.on("update", data => {
    // Обновляем резонанс до перерисовки глобуса
    if (data.resonance) {
        setResonance(data.resonance.resonance);
    }

    updateObjects(data.objects);
    updateUI(data.stats, data.aksi, data.events, data.resonance, data.dimax);

    // Обновляем тепловую карту если пришла
    if (data.heatmap) {
        updateHeatmap(data.heatmap);
    }

    // Обновляем Memory_AKSI снапшоты
    if (data.memoryUpdate) {
        updateMemory(data.memoryUpdate);
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

// Memory_AKSI при подключении
socket.on("memory", data => {
    updateMemory(data);
});

// Перерисовываем глобус при изменении размера окна
window.addEventListener("resize", () => {
    drawGlobe();
});

// Инициализируем UI-компоненты после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    initReplayButton();
    initSemanticSearch();
});

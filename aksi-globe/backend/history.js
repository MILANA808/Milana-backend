// history.js — сохранение истории состояний мира AKSI Globe
// Хранит снимки (snapshots) в памяти и записывает в файл
// Снимок: { ts, aksi, stats, eventCount, topRoles }

const fs = require("fs");
const path = require("path");

const MAX_IN_MEMORY = 1000;      // максимум снимков в памяти
const SAVE_INTERVAL_MS = 60000;  // сохраняем на диск каждую минуту
const HISTORY_FILE = path.join(__dirname, "../data/history.jsonl");

let snapshots = [];
let lastSaved = 0;

// Гарантируем наличие папки data/
function ensureDir() {
    const dir = path.dirname(HISTORY_FILE);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}

// Добавить снимок в историю
exports.record = function(stats, aksi, events) {
    const snapshot = {
        ts: Date.now(),
        aksi: aksi ? parseFloat(aksi.aksi.toFixed(4)) : 0,
        A: aksi ? parseFloat(aksi.A.toFixed(3)) : 0,
        I: aksi ? parseFloat(aksi.I.toFixed(3)) : 0,
        S: aksi ? parseFloat(aksi.S.toFixed(3)) : 0,
        n: aksi ? aksi.n : 0,
        total: stats ? stats.total : 0,
        avgSpeed: stats ? parseFloat((stats.avgSpeed || 0).toFixed(3)) : 0,
        flow: stats ? parseFloat((stats.flow || 0).toFixed(2)) : 0,
        clusterIndex: stats ? parseFloat((stats.clusterIndex || 0).toFixed(3)) : 0,
        entropy: stats ? parseFloat((stats.entropy || 0).toFixed(3)) : 0,
        eventCount: events ? events.length : 0,
        topRoles: stats && stats.roleCounts
            ? Object.entries(stats.roleCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 2)
                .map(([role, count]) => ({ role, count }))
            : []
    };

    snapshots.push(snapshot);

    // Обрезаем до MAX_IN_MEMORY
    if (snapshots.length > MAX_IN_MEMORY) {
        snapshots = snapshots.slice(snapshots.length - MAX_IN_MEMORY);
    }

    // Периодически сохраняем на диск
    const now = Date.now();
    if (now - lastSaved > SAVE_INTERVAL_MS) {
        exports.flush();
        lastSaved = now;
    }
};

// Получить последние N снимков
exports.getLast = function(n) {
    return snapshots.slice(-Math.min(n, snapshots.length));
};

// Получить сводку за всё время
exports.getSummary = function() {
    if (snapshots.length === 0) {
        return { count: 0, avgAksi: 0, maxAksi: 0, minAksi: 0, duration: 0 };
    }

    const aksiValues = snapshots.map(s => s.aksi);
    const avg = aksiValues.reduce((a, b) => a + b, 0) / aksiValues.length;
    const max = Math.max(...aksiValues);
    const min = Math.min(...aksiValues);
    const duration = snapshots[snapshots.length - 1].ts - snapshots[0].ts;

    return {
        count: snapshots.length,
        avgAksi: parseFloat(avg.toFixed(4)),
        maxAksi: parseFloat(max.toFixed(4)),
        minAksi: parseFloat(min.toFixed(4)),
        duration: Math.round(duration / 1000) // секунды
    };
};

// Сохранить снимки на диск (JSONL формат — по одному JSON на строку)
exports.flush = function() {
    try {
        ensureDir();
        const lines = snapshots.map(s => JSON.stringify(s)).join("\n");
        fs.writeFileSync(HISTORY_FILE, lines + "\n", "utf8");
        console.log(`[history] Saved ${snapshots.length} snapshots to disk`);
    } catch (e) {
        console.error("[history] Save error:", e.message);
    }
};

// Загрузить историю с диска при старте
exports.load = function() {
    try {
        ensureDir();
        if (!fs.existsSync(HISTORY_FILE)) return;
        const lines = fs.readFileSync(HISTORY_FILE, "utf8").trim().split("\n");
        const loaded = lines
            .filter(l => l.trim())
            .map(l => {
                try { return JSON.parse(l); } catch { return null; }
            })
            .filter(Boolean);
        snapshots = loaded.slice(-MAX_IN_MEMORY);
        console.log(`[history] Loaded ${snapshots.length} snapshots from disk`);
    } catch (e) {
        console.error("[history] Load error:", e.message);
    }
};

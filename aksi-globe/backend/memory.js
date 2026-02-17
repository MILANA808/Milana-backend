// memory.js — Memory_AKSI (BioMemory-style)
//
// Каждые 10 сек сохраняет snapshot {timestamp, aksi, resonance, objectsCount, topEvent}
// Максимум 100 снапшотов (циклически)
// Эндпоинт /api/memory → возвращает историю

const MAX_SNAPSHOTS = 100;
const SNAPSHOT_INTERVAL_TICKS = 10; // каждые 10 тиков (= 10 сек при 1 тик/сек)

let snapshots = [];
let tickCounter = 0;

/**
 * Записать снапшот если прошло нужное кол-во тиков
 * @param {Object} stats — метрики мира
 * @param {Object} aksiData — данные AKSI
 * @param {Object} resonanceData — данные резонанса
 * @param {Array} events — текущие события
 */
exports.tick = function(stats, aksiData, resonanceData, events) {
    tickCounter++;
    if (tickCounter % SNAPSHOT_INTERVAL_TICKS !== 0) return;

    const topEvent = events && events.length > 0 ? events[0] : null;

    const snapshot = {
        timestamp: Date.now(),
        aksi: aksiData ? parseFloat((aksiData.aksi || 0).toFixed(4)) : 0,
        resonance: resonanceData ? parseFloat((resonanceData.resonance || 0).toFixed(4)) : 0,
        objectsCount: stats ? stats.total : 0,
        topEvent: topEvent ? { type: topEvent.type, label: topEvent.label } : null,
        entropy: aksiData ? parseFloat((aksiData.entropy || 0).toFixed(4)) : 0,
        flow: stats ? parseFloat((stats.flow || 0).toFixed(2)) : 0
    };

    snapshots.push(snapshot);

    // Циклический буфер — удаляем старые снапшоты
    if (snapshots.length > MAX_SNAPSHOTS) {
        snapshots = snapshots.slice(-MAX_SNAPSHOTS);
    }
};

/**
 * Получить все снапшоты (для /api/memory)
 * @returns {Array}
 */
exports.getSnapshots = function() {
    return snapshots.slice();
};

/**
 * Получить последние N снапшотов
 * @param {number} n
 * @returns {Array}
 */
exports.getLast = function(n) {
    return snapshots.slice(-Math.min(n, MAX_SNAPSHOTS));
};

/**
 * Очистить историю
 */
exports.clear = function() {
    snapshots = [];
    tickCounter = 0;
};

/**
 * Получить статистику по памяти
 */
exports.getSummary = function() {
    if (snapshots.length === 0) return { count: 0 };

    const aksiValues = snapshots.map(s => s.aksi);
    const resValues = snapshots.map(s => s.resonance);

    return {
        count: snapshots.length,
        maxSnapshots: MAX_SNAPSHOTS,
        avgAksi: parseFloat((aksiValues.reduce((a, b) => a + b, 0) / aksiValues.length).toFixed(4)),
        maxAksi: parseFloat(Math.max(...aksiValues).toFixed(4)),
        avgResonance: parseFloat((resValues.reduce((a, b) => a + b, 0) / resValues.length).toFixed(4)),
        firstTs: snapshots[0].timestamp,
        lastTs: snapshots[snapshots.length - 1].timestamp
    };
};

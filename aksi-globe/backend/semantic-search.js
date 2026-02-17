// semantic-search.js — Локальный семантический поиск по событиям
//
// Используется cosine similarity на bag-of-words векторах.
// Без внешних зависимостей — всё вычисляется in-process.

// Словарь ключевых слов для bag-of-words векторизации
const VOCAB = [
    "swarm", "scout", "cluster", "signal", "trader",
    "peak", "surge", "active", "high", "low",
    "aksi", "flow", "entropy", "resonance", "detected"
];

/**
 * Создать bag-of-words вектор из строки
 * @param {string} text
 * @returns {number[]}
 */
function textToVector(text) {
    const lower = (text || "").toLowerCase();
    return VOCAB.map(word => {
        // Считаем частоту слова в тексте (0 или 1+ вхождений, нормализованных)
        const regex = new RegExp("\\b" + word + "\\b", "g");
        const matches = lower.match(regex);
        return matches ? matches.length : 0;
    });
}

/**
 * Cosine similarity между двумя векторами
 * @param {number[]} a
 * @param {number[]} b
 * @returns {number} от 0 до 1
 */
function cosineSimilarity(a, b) {
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    const denom = Math.sqrt(normA) * Math.sqrt(normB);
    return denom === 0 ? 0 : dot / denom;
}

// Хранилище проиндексированных событий (последние 50)
const MAX_EVENTS = 50;
let eventHistory = [];

/**
 * Добавить событие в историю для поиска
 * @param {{ type: string, label: string, ts: number, [key: string]: any }} event
 */
exports.indexEvent = function(event) {
    const text = `${event.type} ${event.label || ""} ${Object.values(event).join(" ")}`;
    const vector = textToVector(text);
    eventHistory.push({ event, text, vector, ts: event.ts || Date.now() });
    // Ограничиваем размер буфера
    if (eventHistory.length > MAX_EVENTS) {
        eventHistory = eventHistory.slice(-MAX_EVENTS);
    }
};

/**
 * Найти топ-5 событий по семантическому сходству с запросом
 * @param {string} queryString
 * @returns {Array<{ event: Object, score: number }>}
 */
exports.searchEvents = function(queryString) {
    if (!queryString || eventHistory.length === 0) return [];

    const queryVec = textToVector(queryString);

    const results = eventHistory.map(entry => ({
        event: entry.event,
        text: entry.text,
        score: cosineSimilarity(queryVec, entry.vector)
    }));

    // Сортируем по убыванию score, берём топ-5
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, 5).filter(r => r.score > 0);
};

/**
 * Получить весь индекс событий (для отладки)
 */
exports.getIndexed = function() {
    return eventHistory.map(e => ({ event: e.event, text: e.text }));
};

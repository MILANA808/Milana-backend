// AI module — управление объектами с ролями
// Поддерживает Resonance Field: при высоком резонансе cluster-объекты двигаются быстрее,
// при низком — все объекты замедляются.

const roles = ["scout", "trader", "cluster", "signal"];
const { getResonanceDriftMultiplier } = require("./resonance");

/**
 * Обновить состояние объектов
 * @param {Array} objects — текущие объекты
 * @param {number} resonanceVal — текущий уровень резонанса (0..1)
 * @returns {Array} обновлённые объекты
 */
exports.update = function(objects, resonanceVal = 0.5) {
    // Спавним до 30 объектов с ролями
    if (objects.length < 30) {
        objects.push({
            id: Date.now(),
            lat: (Math.random() * 180) - 90,
            lng: (Math.random() * 360) - 180,
            speed: Math.random() * 5,
            role: roles[Math.floor(Math.random() * roles.length)],
            group: Math.random() > 0.4 ? Math.floor(Math.random() * 5) : null
        });
    }

    return objects.map(o => {
        // Базовый дрейф по роли
        let drift = 0.2;
        if (o.role === "cluster") drift = 0.05;
        if (o.role === "scout")   drift = 0.4;
        if (o.role === "trader")  drift = 0.15;
        if (o.role === "signal")  drift = 0.25;

        // Применяем Resonance Field multiplier
        const multiplier = getResonanceDriftMultiplier(resonanceVal, o.role);
        drift *= multiplier;

        let newLat = o.lat + (Math.random() - 0.5) * drift;
        let newLng = o.lng + (Math.random() - 0.5) * drift;

        // Держим координаты в допустимом диапазоне
        newLat = Math.max(-90, Math.min(90, newLat));
        if (newLng > 180) newLng -= 360;
        if (newLng < -180) newLng += 360;

        return { ...o, lat: newLat, lng: newLng };
    });
};

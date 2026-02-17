// globe.js — 3D визуализация Земли с объектами, цветами ролей, тепловой картой и Resonance Field

// Цвета по роли объекта
const roleColors = {
    scout:   { fill: "#00ff88", glow: "rgba(0, 255, 136, 0.9)" },
    trader:  { fill: "#00ccff", glow: "rgba(0, 204, 255, 0.9)" },
    cluster: { fill: "#ffaa00", glow: "rgba(255, 170, 0, 0.9)" },
    signal:  { fill: "#ff44ff", glow: "rgba(255, 68, 255, 0.9)" },
    default: { fill: "#00ff80", glow: "rgba(0, 255, 128, 0.9)" }
};

// Тепловые точки накопленные от сервера
let hotspots = [];

// Текущий уровень резонанса (0..1)
let currentResonance = 0;

// Конвертация lat/lng → canvas xy для глобуса
function latLngToXY(lat, lng, cx, cy, rx, ry) {
    const normLng = (lng + 180) / 360;
    const normLat = (90 - lat) / 180;

    const angle = normLng * Math.PI * 2 - Math.PI;
    const latFrac = normLat * 2 - 1;

    const cosA = Math.cos(angle);
    if (cosA < 0) return null; // задняя полусфера

    const x = cx + Math.cos(angle) * rx * Math.cos(latFrac * Math.PI / 2);
    const y = cy + latFrac * ry;

    return { x, y };
}

export function drawGlobe() {
    const canvas = document.getElementById("globe");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Фон — космос
    ctx.fillStyle = "#0a0a1a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Звёзды
    for (let i = 0; i < 200; i++) {
        const sx = Math.random() * canvas.width;
        const sy = Math.random() * canvas.height;
        const sr = Math.random() * 1.2;
        ctx.beginPath();
        ctx.arc(sx, sy, sr, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.7 + 0.3})`;
        ctx.fill();
    }

    // Земля — эллипс с градиентом
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const rx = Math.min(canvas.width, canvas.height) * 0.38;
    const ry = rx * 0.9;

    const gradient = ctx.createRadialGradient(cx - rx * 0.3, cy - ry * 0.3, rx * 0.1, cx, cy, rx);
    gradient.addColorStop(0, "#1a6fa0");
    gradient.addColorStop(0.5, "#0d4a73");
    gradient.addColorStop(1, "#071e30");

    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Resonance Field аура вокруг глобуса (при высоком резонансе)
    if (currentResonance > 0.4) {
        const hue = Math.round(currentResonance * 240); // red → blue
        const alpha = (currentResonance - 0.4) * 0.4;
        const auraGrad = ctx.createRadialGradient(cx, cy, rx * 0.95, cx, cy, rx * 1.25);
        auraGrad.addColorStop(0, `hsla(${hue}, 80%, 60%, ${alpha})`);
        auraGrad.addColorStop(1, "rgba(0,0,0,0)");

        ctx.beginPath();
        ctx.ellipse(cx, cy, rx * 1.25, ry * 1.25, 0, 0, Math.PI * 2);
        ctx.fillStyle = auraGrad;
        ctx.fill();
    }

    // Тепловая карта (рисуем поверх Земли, до сетки)
    if (hotspots.length > 0) {
        const maxVal = Math.max(...hotspots.map(h => h.value), 1);
        hotspots.forEach(h => {
            const pos = latLngToXY(h.lat, h.lng, cx, cy, rx, ry);
            if (!pos) return;

            const intensity = h.value / maxVal;
            const radius = 15 + intensity * 30;
            const alpha = 0.05 + intensity * 0.25;

            const heatGlow = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, radius);
            heatGlow.addColorStop(0, `rgba(255, 100, 0, ${alpha})`);
            heatGlow.addColorStop(1, "rgba(255, 100, 0, 0)");

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = heatGlow;
            ctx.fill();
        });
    }

    // Сетка координат
    ctx.strokeStyle = "rgba(0, 200, 255, 0.12)";
    ctx.lineWidth = 0.5;

    // Широты
    for (let lat = -60; lat <= 60; lat += 30) {
        const yOff = (lat / 90) * ry;
        const xScale = Math.sqrt(1 - (yOff / ry) ** 2);
        ctx.beginPath();
        ctx.ellipse(cx, cy + yOff, rx * xScale, ry * 0.1, 0, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Долготы
    for (let lng = 0; lng < 180; lng += 30) {
        const angle = (lng / 180) * Math.PI;
        const x1 = cx + Math.cos(angle) * rx;
        const x2 = cx - Math.cos(angle) * rx;
        ctx.beginPath();
        ctx.moveTo(x1, cy);
        ctx.bezierCurveTo(x1, cy - ry, x2, cy - ry, x2, cy);
        ctx.bezierCurveTo(x2, cy + ry, x1, cy + ry, x1, cy);
        ctx.stroke();
    }

    window._globeGeometry = { cx, cy, rx, ry };
}

export function updateObjects(objects) {
    const canvas = document.getElementById("globe");
    const ctx = canvas.getContext("2d");

    // Перерисовываем глобус (включая тепловую карту и ауру резонанса)
    drawGlobe();

    if (!objects || objects.length === 0) return;

    const { cx, cy, rx, ry } = window._globeGeometry || { cx: canvas.width / 2, cy: canvas.height / 2, rx: 200, ry: 180 };

    objects.forEach(o => {
        const pos = latLngToXY(o.lat, o.lng, cx, cy, rx, ry);
        if (!pos) return;

        const { x, y } = pos;

        // Цвет по роли
        const color = roleColors[o.role] || roleColors.default;

        // Усиленный glow при высоком резонансе
        const glowRadius = currentResonance > 0.7 ? 16 : 10;

        const glow = ctx.createRadialGradient(x, y, 0, x, y, glowRadius);
        glow.addColorStop(0, color.glow);
        glow.addColorStop(1, "rgba(0, 0, 0, 0)");

        ctx.beginPath();
        ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        // Точка объекта
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = color.fill;
        ctx.shadowColor = color.fill;
        ctx.shadowBlur = currentResonance > 0.7 ? 18 : 10;
        ctx.fill();
        ctx.shadowBlur = 0;
    });
}

// Обновить кешированные тепловые точки
export function updateHeatmap(data) {
    if (data && Array.isArray(data)) {
        hotspots = data;
    }
}

// Обновить текущий уровень резонанса для рендеринга
export function setResonance(val) {
    currentResonance = val || 0;
}

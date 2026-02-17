// heatmap.js — карта тепловой активности AKSI Globe
// Аккумулирует позиции объектов в сетку и возвращает данные для тепловой карты

// Размер сетки
const GRID_LAT = 36;  // 36 ячеек по широте (шаг 5°)
const GRID_LNG = 72;  // 72 ячейки по долготе (шаг 5°)
const DECAY_FACTOR = 0.95; // затухание тепла каждый тик

// Сетка накопления активности [lat_index][lng_index] = value
let grid = Array.from({ length: GRID_LAT }, () => new Float32Array(GRID_LNG));

// Обновить карту тепла по новому набору объектов
exports.update = function(objects) {
    // Затухание предыдущих значений
    for (let i = 0; i < GRID_LAT; i++) {
        for (let j = 0; j < GRID_LNG; j++) {
            grid[i][j] *= DECAY_FACTOR;
        }
    }

    // Добавляем тепло по текущим позициям
    objects.forEach(o => {
        const latIdx = Math.floor((o.lat + 90) / 180 * GRID_LAT);
        const lngIdx = Math.floor((o.lng + 180) / 360 * GRID_LNG);

        const li = Math.max(0, Math.min(GRID_LAT - 1, latIdx));
        const lj = Math.max(0, Math.min(GRID_LNG - 1, lngIdx));

        // Интенсивность = скорость / 10 (нормализуем)
        const intensity = Math.min(1, (o.speed || 1) / 10);
        grid[li][lj] = Math.min(10, grid[li][lj] + intensity);
    });
};

// Вернуть разреженный список горячих точек (ненулевые ячейки)
exports.getHotspots = function(threshold) {
    threshold = threshold || 0.1;
    const hotspots = [];

    for (let i = 0; i < GRID_LAT; i++) {
        for (let j = 0; j < GRID_LNG; j++) {
            const val = grid[i][j];
            if (val >= threshold) {
                // Конвертируем индексы обратно в координаты (центр ячейки)
                const lat = (i / GRID_LAT) * 180 - 90 + (180 / GRID_LAT / 2);
                const lng = (j / GRID_LNG) * 360 - 180 + (360 / GRID_LNG / 2);
                hotspots.push({ lat, lng, value: parseFloat(val.toFixed(3)) });
            }
        }
    }

    return hotspots;
};

// Сбросить карту
exports.reset = function() {
    grid = Array.from({ length: GRID_LAT }, () => new Float32Array(GRID_LNG));
};

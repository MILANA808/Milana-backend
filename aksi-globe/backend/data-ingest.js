// data-ingest.js — адаптер для реальных источников данных
// Источники: OpenSky API (самолёты), AIS (корабли), публичные данные дронов
// Адаптер нормализует внешние данные к формату объектов AKSI Globe

const https = require("https");

// Нормализация объекта к внутреннему формату
function normalizeObject(raw, source) {
    const base = {
        id: raw.id || raw.icao24 || raw.mmsi || `${source}-${Date.now()}-${Math.random()}`,
        lat: parseFloat(raw.lat || raw.latitude || raw.lat_deg || 0),
        lng: parseFloat(raw.lng || raw.longitude || raw.lon_deg || raw.lon || 0),
        speed: parseFloat(raw.speed || raw.velocity || raw.sog || 0),
        source: source,
        group: raw.group || null,
        role: null
    };

    // Назначаем роль по типу источника
    if (source === "opensky") {
        // Самолёты: быстрые → scout или trader
        base.role = base.speed > 200 ? "scout" : "trader";
    } else if (source === "ais") {
        // Корабли: медленные → cluster
        base.role = base.speed < 5 ? "cluster" : "trader";
    } else if (source === "drone") {
        // Дроны → signal
        base.role = "signal";
    } else {
        // По умолчанию — trader
        base.role = "trader";
    }

    return base;
}

// OpenSky Network API — реальные позиции самолётов
// Документация: https://opensky-network.org/apidoc/rest.html
function fetchOpenSky(callback) {
    const options = {
        hostname: "opensky-network.org",
        path: "/api/states/all?lamin=-30&lomin=-60&lamax=60&lomax=60",
        method: "GET",
        headers: { "User-Agent": "AKSI-Globe/1.0" },
        timeout: 5000
    };

    const req = https.request(options, (res) => {
        let data = "";
        res.on("data", chunk => data += chunk);
        res.on("end", () => {
            try {
                const json = JSON.parse(data);
                if (!json.states) return callback(null, []);

                const objects = json.states
                    .filter(s => s[5] !== null && s[6] !== null) // только с координатами
                    .slice(0, 20) // ограничиваем до 20 самолётов
                    .map(s => normalizeObject({
                        id: s[0],         // icao24
                        lng: s[5],        // longitude
                        lat: s[6],        // latitude
                        speed: (s[9] || 0) * 3.6 // velocity m/s → km/h
                    }, "opensky"));

                callback(null, objects);
            } catch (e) {
                callback(e, []);
            }
        });
    });

    req.on("error", err => callback(err, []));
    req.on("timeout", () => { req.destroy(); callback(new Error("OpenSky timeout"), []); });
    req.end();
}

// AIS Web API — реальные позиции кораблей (публичный endpoint)
// Используем AISHub или MarineTraffic-совместимый формат
function fetchAIS(callback) {
    // Публичный источник NOAA/MarineTraffic для демо
    const options = {
        hostname: "www.seatemperature.org",
        path: "/api/ships.json",
        method: "GET",
        headers: { "User-Agent": "AKSI-Globe/1.0" },
        timeout: 5000
    };

    const req = https.request(options, (res) => {
        let data = "";
        res.on("data", chunk => data += chunk);
        res.on("end", () => {
            try {
                const json = JSON.parse(data);
                const ships = Array.isArray(json) ? json : (json.ships || json.vessels || []);
                const objects = ships
                    .slice(0, 10)
                    .map(s => normalizeObject({
                        mmsi: s.mmsi || s.id,
                        lat: s.lat || s.latitude,
                        lng: s.lon || s.lng || s.longitude,
                        speed: s.sog || s.speed || 0
                    }, "ais"));
                callback(null, objects);
            } catch (e) {
                callback(e, []);
            }
        });
    });

    req.on("error", err => callback(err, []));
    req.on("timeout", () => { req.destroy(); callback(new Error("AIS timeout"), []); });
    req.end();
}

// Генерация симулированных данных для источника (если реальный API недоступен)
function generateFallback(source, count) {
    const roles = { opensky: "scout", ais: "cluster", drone: "signal" };
    return Array.from({ length: count }, (_, i) => ({
        id: `${source}-sim-${i}`,
        lat: (Math.random() * 180) - 90,
        lng: (Math.random() * 360) - 180,
        speed: source === "opensky" ? 400 + Math.random() * 400 : Math.random() * 20,
        source: source + "-sim",
        role: roles[source] || "trader",
        group: null
    }));
}

// Основная функция — пробуем реальный API, при ошибке → fallback симуляция
exports.ingest = function(callback) {
    const results = [];
    let pending = 1;

    function done(err, objects) {
        if (objects && objects.length > 0) {
            results.push(...objects);
        } else if (err) {
            console.log(`[data-ingest] API error: ${err.message} — using simulation fallback`);
        }
        pending--;
        if (pending === 0) {
            // Если ничего не получили — возвращаем fallback данные
            if (results.length === 0) {
                results.push(...generateFallback("opensky", 5));
                results.push(...generateFallback("ais", 3));
                results.push(...generateFallback("drone", 2));
            }
            callback(null, results);
        }
    }

    // Пробуем OpenSky API
    fetchOpenSky(done);
};

exports.normalizeObject = normalizeObject;
exports.generateFallback = generateFallback;

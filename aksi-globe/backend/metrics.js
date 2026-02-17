// metrics.js — расширенные метрики мира AKSI Globe
//
// Метрики мира:
//   density      = objects / area        (насыщенность пространства)
//   entropy      = разнообразие ролей    (Шеннон)
//   flow         = суммарная скорость    (общий поток мира)
//   clusterIndex = доля сгруппированных  (координация групп)
//
// Метрики поведения:
//   trajectoryVariance = дисперсия дрейфа
//   interactionRate    = объекты в группах / total
//   signalIntensity    = интенсивность сигналов
//
// DIMAX v3 (реал-тайм метрика симуляции):
//   DIMAX = (D × I × √AX × 0.75 + M × 1.3 + Balance_bonus + SSB) / 3.5
//   D = Depth   = resonance + entropy (нормализовано 0-1)
//   I = Impact  = AKSI × objectsCount / 100
//   AX = Acceleration = скорость роста AKSI за последние 30 сек
//   M = Materialization = 0.85 (статично)
//   Balance_bonus = 0.08 × (1 - max_axis + min_axis)
//   SSB = 0.15 (статично)

// Хранит последние 30 значений AKSI для расчёта ускорения
const aksiBuf = [];
const AX_WINDOW = 30;

exports.calc = function(objects) {
    const n = objects.length || 1;

    // --- Базовые метрики ---
    const totalSpeed = objects.reduce((a, b) => a + (b.speed || 0), 0);
    const avgSpeed = totalSpeed / n;

    // density: объектов на единицу поверхности (Земля ≈ 510 млн км²)
    const area = 510;
    const density = objects.length / area;

    // flow: суммарная скорость (общая кинетическая активность)
    const flow = totalSpeed;

    // --- Энтропия ролей (Шеннон) ---
    const roleCounts = {};
    objects.forEach(o => {
        const r = o.role || "unknown";
        roleCounts[r] = (roleCounts[r] || 0) + 1;
    });
    const roleKeys = Object.keys(roleCounts);
    const entropy = roleKeys.length > 0
        ? -roleKeys.reduce((sum, r) => {
            const p = roleCounts[r] / n;
            return sum + (p > 0 ? p * Math.log2(p) : 0);
        }, 0)
        : 0;

    // --- Индекс кластеризации ---
    const grouped = objects.filter(o => o.group != null).length;
    const clusterIndex = grouped / n;

    // --- Метрики поведения ---

    // interactionRate: доля объектов в группах
    const interactionRate = clusterIndex;

    // signalIntensity: доля объектов с ролью "signal"
    const signals = objects.filter(o => o.role === "signal").length;
    const signalIntensity = signals / n;

    // trajectoryVariance: дисперсия скоростей
    const meanSpeed = avgSpeed;
    const speedVariance = objects.reduce((sum, o) => {
        const diff = (o.speed || 0) - meanSpeed;
        return sum + diff * diff;
    }, 0) / n;
    const trajectoryVariance = Math.sqrt(speedVariance);

    return {
        total: objects.length,
        avgSpeed,
        density,
        flow,
        entropy,
        clusterIndex,
        interactionRate,
        signalIntensity,
        trajectoryVariance,
        roleCounts
    };
};

/**
 * Рассчитать DIMAX v3 — реал-тайм метрику симуляции
 * @param {Object} stats     — результат calc()
 * @param {Object} aksiData  — результат calcAKSI()
 * @param {Object} resonance — результат calcResonance()
 * @returns {Object} dimax breakdown
 */
exports.calcDIMAX = function(stats, aksiData, resonanceData) {
    const aksiVal = aksiData ? (aksiData.aksi || 0) : 0;

    // Буфер для расчёта ускорения (AX)
    aksiBuf.push(aksiVal);
    if (aksiBuf.length > AX_WINDOW) aksiBuf.shift();

    // AX: скорость роста AKSI за последние 30 сек
    // = (последнее значение - первое) / количество шагов, нормализовано к [0,1]
    let AX = 0;
    if (aksiBuf.length >= 2) {
        const delta = aksiBuf[aksiBuf.length - 1] - aksiBuf[0];
        AX = Math.max(0, Math.min(1, (delta + 1) / 2)); // нормализация -1..1 → 0..1
    } else {
        AX = 0.5; // нейтральное ускорение при нехватке данных
    }

    const resonanceVal = resonanceData ? (resonanceData.resonance || 0) : 0;
    const entropyNorm = Math.min(1, (stats ? stats.entropy || 0 : 0) / Math.log2(4));

    // D = Depth = resonance + entropy (нормализовано 0-1)
    const D = Math.min(1, (resonanceVal + entropyNorm) / 2);

    // I = Impact = AKSI × objectsCount / 100
    const I = Math.min(1, aksiVal * (stats ? stats.total : 0) / 100);

    // M = Materialization (статично)
    const M = 0.85;

    // Balance_bonus = 0.08 × (1 - max_axis + min_axis)
    // Оси: D, I, AX (нормализованы 0..1)
    const axes = [D, I, AX];
    const maxAxis = Math.max(...axes);
    const minAxis = Math.min(...axes);
    const Balance_bonus = 0.08 * (1 - maxAxis + minAxis);

    // SSB = уникальность (статично)
    const SSB = 0.15;

    // DIMAX = (D × I × √AX × 0.75 + M × 1.3 + Balance_bonus + SSB) / 3.5
    const dimax = (D * I * Math.sqrt(AX) * 0.75 + M * 1.3 + Balance_bonus + SSB) / 3.5;

    return {
        dimax: parseFloat(Math.max(0, dimax).toFixed(4)),
        axes: {
            D: parseFloat(D.toFixed(4)),
            I: parseFloat(I.toFixed(4)),
            AX: parseFloat(AX.toFixed(4)),
            M: parseFloat(M.toFixed(4)),
            Balance_bonus: parseFloat(Balance_bonus.toFixed(4)),
            SSB: parseFloat(SSB.toFixed(4))
        }
    };
};

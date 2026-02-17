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

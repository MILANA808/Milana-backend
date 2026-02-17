// AKSI Core — метрики сознательной симуляции
// A = внимание (насыщенность мира)
// I = искренность (динамика системы)
// S = согласие (координация / ролевая группировка)
// AKSI = (A×I×S) × g(n), где g(n) = 1 + γ√n

exports.calcAKSI = function(objects) {
    const n = objects.length;

    const A = Math.min(1, n / 50); // внимание = насыщенность мира

    const totalSpeed = objects.reduce((s, o) => s + o.speed, 0);
    const I = Math.min(1, totalSpeed / (n * 5 || 1)); // искренность = динамика

    const grouped = objects.filter(o => o.group).length;
    const S = Math.min(1, grouped / (n || 1)); // согласие = координация

    const gamma = 0.4;
    const g = 1 + gamma * Math.sqrt(n);

    const aksi = Math.pow(A * I * S, 1) * g;

    // Дополнительные метрики мира
    const roleCounts = {};
    objects.forEach(o => {
        if (o.role) roleCounts[o.role] = (roleCounts[o.role] || 0) + 1;
    });

    const roles = Object.keys(roleCounts);
    const entropy = roles.length > 0
        ? -roles.reduce((sum, r) => {
            const p = roleCounts[r] / (n || 1);
            return sum + (p > 0 ? p * Math.log2(p) : 0);
        }, 0)
        : 0;

    return { A, I, S, n, aksi, g, roleCounts, entropy };
};

// resonance.js — Resonance Field (эмоциональный резонанс)
//
// Resonance = энтропия_ролей × (AKSI / max_AKSI) × diversity_factor
// diversity_factor = 1 - (доминирующая_роль / total)
//
// Эффекты:
//   resonance > 0.7 — glow-эффект и +10% скорость clustering
//   resonance < 0.3 — объекты "затухают" (медленнее дрейф)

const MAX_AKSI = 3.0; // теоретический максимум AKSI

/**
 * Рассчитать Resonance Field на основе состояния мира
 * @param {Object} aksiData — результат calcAKSI()
 * @returns {{ resonance: number, level: string, diversityFactor: number }}
 */
exports.calcResonance = function(aksiData) {
    if (!aksiData || aksiData.n === 0) {
        return { resonance: 0, level: "low", diversityFactor: 0 };
    }

    const { aksi, entropy, roleCounts, n } = aksiData;

    // Нормализованный AKSI (0..1)
    const aksiNorm = Math.min(1, aksi / MAX_AKSI);

    // Энтропия нормализована: максимум log2(4) ≈ 2 для 4 ролей
    const maxEntropy = Math.log2(4);
    const entropyNorm = Math.min(1, (entropy || 0) / maxEntropy);

    // Diversity factor: 1 - доминирующая_роль / total
    const roleValues = Object.values(roleCounts || {});
    const dominantCount = roleValues.length > 0 ? Math.max(...roleValues) : 0;
    const diversityFactor = n > 0 ? 1 - dominantCount / n : 0;

    // Resonance = энтропия × (aksi / max) × diversity
    const resonance = Math.min(1, entropyNorm * aksiNorm * diversityFactor);

    // Уровень резонанса
    let level = "medium";
    if (resonance > 0.7) level = "high";
    else if (resonance < 0.3) level = "low";

    return { resonance, level, diversityFactor, aksiNorm, entropyNorm };
};

/**
 * Применить эффект резонанса к объектам (drift modifier)
 * @param {number} resonance
 * @param {string} role
 * @returns {number} multiplier (0.5 — затухание, 1.1 — усиление)
 */
exports.getResonanceDriftMultiplier = function(resonance, role) {
    if (resonance > 0.7) {
        // Высокий резонанс: cluster-объекты двигаются быстрее
        return role === "cluster" ? 1.1 : 1.0;
    } else if (resonance < 0.3) {
        // Низкий резонанс: всё замедляется
        return 0.7;
    }
    return 1.0;
};

// Events module — генерация событий на основе состояния мира

exports.generate = function(objects, aksiData) {
    const events = [];
    const n = objects.length;

    // Событие роя — слишком много объектов
    if (n > 20) {
        events.push({
            type: "swarm",
            label: "Swarm detected",
            strength: (n / 30).toFixed(2),
            ts: Date.now()
        });
    }

    // Событие высокой динамики — быстрые объекты
    const scouts = objects.filter(o => o.role === "scout");
    if (scouts.length > 5) {
        events.push({
            type: "scout_surge",
            label: "Scout surge",
            count: scouts.length,
            ts: Date.now()
        });
    }

    // Событие кластеризации
    const clusters = objects.filter(o => o.role === "cluster");
    if (clusters.length > 3) {
        events.push({
            type: "clustering",
            label: "Clustering active",
            count: clusters.length,
            ts: Date.now()
        });
    }

    // Событие высокого AKSI индекса
    if (aksiData && aksiData.aksi > 0.5) {
        events.push({
            type: "aksi_peak",
            label: "AKSI peak",
            value: aksiData.aksi.toFixed(3),
            ts: Date.now()
        });
    }

    // Возвращаем только последние 5 событий
    return events.slice(0, 5);
};

// AI module — управление объектами с ролями
const roles = ["scout", "trader", "cluster", "signal"];

exports.update = function(objects) {
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
        // Дрейф зависит от роли
        let drift = 0.2;
        if (o.role === "cluster") drift = 0.05;
        if (o.role === "scout")   drift = 0.4;
        if (o.role === "trader")  drift = 0.15;
        if (o.role === "signal")  drift = 0.25;

        let newLat = o.lat + (Math.random() - 0.5) * drift;
        let newLng = o.lng + (Math.random() - 0.5) * drift;

        // Держим координаты в допустимом диапазоне
        newLat = Math.max(-90, Math.min(90, newLat));
        if (newLng > 180) newLng -= 360;
        if (newLng < -180) newLng += 360;

        return { ...o, lat: newLat, lng: newLng };
    });
};

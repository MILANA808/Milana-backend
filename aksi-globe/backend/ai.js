exports.update = function(objects) {
    if (objects.length < 20) {
        objects.push({
            id: Date.now(),
            lat: (Math.random() * 180) - 90,
            lng: (Math.random() * 360) - 180,
            speed: Math.random() * 5,
        });
    }

    return objects.map(o => ({
        ...o,
        lat: o.lat + (Math.random() - 0.5) * 0.2,
        lng: o.lng + (Math.random() - 0.5) * 0.2
    }));
};

exports.calc = function(objects) {
    return {
        total: objects.length,
        avgSpeed:
            objects.reduce((a, b) => a + b.speed, 0) / (objects.length || 1),
        density: objects.length / 510 // Earth surface area (million km²) approximation
    };
};

export function drawGlobe() {
    const canvas = document.getElementById("globe");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Draw space background
    ctx.fillStyle = "#0a0a1a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw Earth ellipse
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const rx = Math.min(canvas.width, canvas.height) * 0.38;
    const ry = rx * 0.9;

    const gradient = ctx.createRadialGradient(cx - rx * 0.3, cy - ry * 0.3, rx * 0.1, cx, cy, rx);
    gradient.addColorStop(0, "#1a6fa0");
    gradient.addColorStop(0.5, "#0d4a73");
    gradient.addColorStop(1, "#071e30");

    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw grid lines
    ctx.strokeStyle = "rgba(0, 200, 255, 0.12)";
    ctx.lineWidth = 0.5;

    // Latitude lines
    for (let lat = -60; lat <= 60; lat += 30) {
        const yOff = (lat / 90) * ry;
        const xScale = Math.sqrt(1 - (yOff / ry) ** 2);
        ctx.beginPath();
        ctx.ellipse(cx, cy + yOff, rx * xScale, ry * 0.1, 0, 0, Math.PI * 2);
        ctx.stroke();
    }

    // Longitude lines
    for (let lng = 0; lng < 180; lng += 30) {
        const angle = (lng / 180) * Math.PI;
        const x1 = cx + Math.cos(angle) * rx;
        const x2 = cx - Math.cos(angle) * rx;
        ctx.beginPath();
        ctx.moveTo(x1, cy);
        ctx.bezierCurveTo(x1, cy - ry, x2, cy - ry, x2, cy);
        ctx.bezierCurveTo(x2, cy + ry, x1, cy + ry, x1, cy);
        ctx.stroke();
    }

    window._globeGeometry = { cx, cy, rx, ry };
}

export function updateObjects(objects) {
    const canvas = document.getElementById("globe");
    const ctx = canvas.getContext("2d");

    // Redraw globe
    drawGlobe();

    if (!objects || objects.length === 0) return;

    const { cx, cy, rx, ry } = window._globeGeometry || { cx: canvas.width / 2, cy: canvas.height / 2, rx: 200, ry: 180 };

    objects.forEach(o => {
        // Map lat/lng to canvas coordinates (simple equirectangular projection on ellipse)
        const normLng = (o.lng + 180) / 360; // 0..1
        const normLat = (90 - o.lat) / 180;   // 0..1

        // Convert to ellipse coordinates
        const angle = normLng * Math.PI * 2 - Math.PI;
        const latFrac = normLat * 2 - 1; // -1..1

        // Only show front hemisphere (cos > 0)
        const cosA = Math.cos(angle);
        if (cosA < 0) return;

        const x = cx + Math.cos(angle) * rx * Math.cos(latFrac * Math.PI / 2);
        const y = cy + latFrac * ry;

        // Object glow
        const glow = ctx.createRadialGradient(x, y, 0, x, y, 8);
        glow.addColorStop(0, "rgba(0, 255, 128, 0.9)");
        glow.addColorStop(1, "rgba(0, 255, 128, 0)");

        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#00ff80";
        ctx.shadowColor = "#00ff80";
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
    });
}

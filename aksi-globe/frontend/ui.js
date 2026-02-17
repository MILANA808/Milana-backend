// UI module — панель метрик с AKSI индексом, событиями и историей

let historyData = [];

// Обновить главную панель метрик
export function updateUI(stats, aksi, events) {
    if (!stats) return;

    const aksiSection = aksi ? `
        <div class="divider"></div>
        <div class="metric"><span class="label">AKSI Index:</span><span class="value aksi-value">${aksi.aksi.toFixed(3)}</span></div>
        <div class="metric"><span class="label">A (внимание):</span><span class="value">${aksi.A.toFixed(2)}</span></div>
        <div class="metric"><span class="label">I (динамика):</span><span class="value">${aksi.I.toFixed(2)}</span></div>
        <div class="metric"><span class="label">S (согласие):</span><span class="value">${aksi.S.toFixed(2)}</span></div>
        <div class="metric"><span class="label">Энтропия:</span><span class="value">${aksi.entropy ? aksi.entropy.toFixed(2) : "0.00"}</span></div>
    ` : "";

    const worldSection = `
        <div class="divider"></div>
        <div class="metric"><span class="label">Поток:</span><span class="value">${(stats.flow || 0).toFixed(1)}</span></div>
        <div class="metric"><span class="label">Кластеры:</span><span class="value">${((stats.clusterIndex || 0) * 100).toFixed(0)}%</span></div>
        <div class="metric"><span class="label">Сигналы:</span><span class="value">${((stats.signalIntensity || 0) * 100).toFixed(0)}%</span></div>
        <div class="metric"><span class="label">Дисперсия:</span><span class="value">${(stats.trajectoryVariance || 0).toFixed(2)}</span></div>
    `;

    const rolesSection = aksi && aksi.roleCounts ? `
        <div class="divider"></div>
        <div class="metric small"><span class="label scout">● scout:</span><span class="value">${aksi.roleCounts.scout || 0}</span></div>
        <div class="metric small"><span class="label trader">● trader:</span><span class="value">${aksi.roleCounts.trader || 0}</span></div>
        <div class="metric small"><span class="label cluster">● cluster:</span><span class="value">${aksi.roleCounts.cluster || 0}</span></div>
        <div class="metric small"><span class="label signal">● signal:</span><span class="value">${aksi.roleCounts.signal || 0}</span></div>
    ` : "";

    const eventsSection = events && events.length > 0 ? `
        <div class="divider"></div>
        <div class="events-title">События:</div>
        ${events.map(e => `<div class="event">${e.label}</div>`).join("")}
    ` : "";

    document.getElementById("ui").innerHTML = `
    <div class="panel">
        <div class="panel-title">AKSI Globe</div>
        <div class="metric"><span class="label">Объектов:</span><span class="value">${stats.total}</span></div>
        <div class="metric"><span class="label">Ср. скорость:</span><span class="value">${stats.avgSpeed.toFixed(2)}</span></div>
        <div class="metric"><span class="label">Плотность:</span><span class="value">${stats.density.toFixed(4)}</span></div>
        ${aksiSection}
        ${worldSection}
        ${rolesSection}
        ${eventsSection}
        <div class="status">● LIVE</div>
    </div>`;
}

// Обновить мини-график истории AKSI
export function updateHistory(snapshots) {
    if (!snapshots || snapshots.length === 0) return;
    historyData = snapshots;

    const canvas = document.getElementById("history-chart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth || 200;
    canvas.height = 60;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Фон
    ctx.fillStyle = "rgba(0, 20, 40, 0.8)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Ось Y 0..1
    const maxAksi = 1;
    const w = canvas.width;
    const h = canvas.height;
    const data = historyData.slice(-100);

    if (data.length < 2) return;

    // Линия AKSI
    ctx.beginPath();
    ctx.strokeStyle = "#00ccff";
    ctx.lineWidth = 1.5;

    data.forEach((s, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - (s.aksi / maxAksi) * h * 0.9 - h * 0.05;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Метка последнего значения
    const last = data[data.length - 1];
    ctx.fillStyle = "#00ccff";
    ctx.font = "10px monospace";
    ctx.fillText(`AKSI: ${last.aksi.toFixed(3)}`, 4, 12);

    // Длительность
    if (data.length > 1) {
        const duration = Math.round((data[data.length - 1].ts - data[0].ts) / 1000);
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.fillText(`${duration}s`, w - 30, 12);
    }
}

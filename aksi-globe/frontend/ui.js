// UI module — панель метрик с AKSI индексом и событиями

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
        ${rolesSection}
        ${eventsSection}
        <div class="status">● LIVE</div>
    </div>`;
}

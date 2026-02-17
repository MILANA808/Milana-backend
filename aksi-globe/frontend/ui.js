export function updateUI(stats) {
    if (!stats) return;
    document.getElementById("ui").innerHTML = `
    <div class="panel">
        <div class="panel-title">AKSI Globe</div>
        <div class="metric"><span class="label">Objects:</span><span class="value">${stats.total}</span></div>
        <div class="metric"><span class="label">Avg speed:</span><span class="value">${stats.avgSpeed.toFixed(2)}</span></div>
        <div class="metric"><span class="label">Density:</span><span class="value">${stats.density.toFixed(4)}</span></div>
        <div class="status">● LIVE</div>
    </div>`;
}

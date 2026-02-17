// UI module — панель метрик с AKSI индексом, Resonance, DIMAX v3, событиями и историей

let historyData = [];
let memoryData = [];
let isReplayingMemory = false;
let replayIndex = 0;
let replayTimer = null;

// --- Основная панель ---

/** @param {Object} stats @param {Object} aksi @param {Array} events @param {Object} res @param {Object} dimax */
export function updateUI(stats, aksi, events, resonanceData, dimaxData) {
    if (!stats) return;

    const aksiSection = aksi ? `
        <div class="divider"></div>
        <div class="metric"><span class="label">AKSI Index:</span><span class="value aksi-value">${aksi.aksi.toFixed(3)}</span></div>
        <div class="metric"><span class="label">A (внимание):</span><span class="value">${aksi.A.toFixed(2)}</span></div>
        <div class="metric"><span class="label">I (динамика):</span><span class="value">${aksi.I.toFixed(2)}</span></div>
        <div class="metric"><span class="label">S (согласие):</span><span class="value">${aksi.S.toFixed(2)}</span></div>
        <div class="metric"><span class="label">Энтропия:</span><span class="value">${aksi.entropy ? aksi.entropy.toFixed(2) : "0.00"}</span></div>
    ` : "";

    // Resonance Field индикатор
    const resonanceSection = resonanceData ? (() => {
        const r = resonanceData.resonance;
        const level = resonanceData.level || "medium";
        const pct = Math.round(r * 100);
        const pulsing = r > 0.8 ? " resonance-pulse" : "";
        // Цвет: красный → синий
        const hue = Math.round(r * 240); // 0=red, 240=blue
        return `
        <div class="divider"></div>
        <div class="metric"><span class="label">Resonance:</span><span class="value resonance-value${pulsing}" style="color: hsl(${hue},90%,60%)">${r.toFixed(3)}</span></div>
        <div class="resonance-bar-wrap"><div class="resonance-bar" style="width:${pct}%; background: hsl(${hue},80%,45%)"></div></div>
        <div class="metric small"><span class="label">Уровень:</span><span class="value" style="color: hsl(${hue},90%,60%)">${level.toUpperCase()}</span></div>
        ` ;
    })() : "";

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
        ${resonanceSection}
        ${worldSection}
        ${rolesSection}
        ${eventsSection}
        <div class="status">● LIVE</div>
    </div>`;

    // Обновить DIMAX v3 панель
    if (dimaxData) updateDIMAX(dimaxData);
}

// --- DIMAX v3 панель ---

/** @param {{ dimax: number, axes: Object }} dimaxData */
export function updateDIMAX(dimaxData) {
    const panel = document.getElementById("dimax-panel");
    if (!panel) return;
    const { dimax, axes } = dimaxData;
    panel.innerHTML = `
        <div class="history-title">DIMAX v3: ${dimax.toFixed(3)}</div>
        <div class="dimax-grid">
            <div class="dimax-axis"><span class="da-label">D</span><span class="da-val">${axes.D.toFixed(3)}</span></div>
            <div class="dimax-axis"><span class="da-label">I</span><span class="da-val">${axes.I.toFixed(3)}</span></div>
            <div class="dimax-axis"><span class="da-label">AX</span><span class="da-val">${axes.AX.toFixed(3)}</span></div>
            <div class="dimax-axis"><span class="da-label">M</span><span class="da-val">${axes.M.toFixed(3)}</span></div>
            <div class="dimax-axis"><span class="da-label">Bal</span><span class="da-val">${axes.Balance_bonus.toFixed(3)}</span></div>
            <div class="dimax-axis"><span class="da-label">SSB</span><span class="da-val">${axes.SSB.toFixed(3)}</span></div>
        </div>
        <div class="dimax-bar-wrap"><div class="dimax-bar" style="width:${Math.min(100, dimax * 100).toFixed(0)}%"></div></div>
    `;
}

// --- Мини-граф истории AKSI ---

export function updateHistory(snapshots) {
    if (!snapshots || snapshots.length === 0) return;
    historyData = snapshots;

    const canvas = document.getElementById("history-chart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    canvas.width = canvas.offsetWidth || 200;
    canvas.height = 60;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "rgba(0, 20, 40, 0.8)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const maxAksi = 1;
    const w = canvas.width;
    const h = canvas.height;
    const data = historyData.slice(-100);

    if (data.length < 2) return;

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

    const last = data[data.length - 1];
    ctx.fillStyle = "#00ccff";
    ctx.font = "10px monospace";
    ctx.fillText(`AKSI: ${last.aksi.toFixed(3)}`, 4, 12);

    if (data.length > 1) {
        const duration = Math.round((data[data.length - 1].ts - data[0].ts) / 1000);
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.fillText(`${duration}s`, w - 30, 12);
    }
}

// --- Memory_AKSI снапшоты и Replay ---

export function updateMemory(snapshots) {
    if (!snapshots || snapshots.length === 0) return;
    memoryData = snapshots;
}

/** Анимированный replay по снапшотам памяти */
function startReplay() {
    if (memoryData.length === 0) return;
    isReplayingMemory = true;
    replayIndex = 0;

    const replayStatus = document.getElementById("replay-status");
    if (replayStatus) replayStatus.textContent = `Replay: ${replayIndex + 1}/${memoryData.length}`;

    if (replayTimer) clearInterval(replayTimer);
    replayTimer = setInterval(() => {
        const snap = memoryData[replayIndex];
        if (!snap) { stopReplay(); return; }

        // Показываем снапшот в мини-панели
        const replayStatus = document.getElementById("replay-status");
        if (replayStatus) {
            const d = new Date(snap.timestamp);
            replayStatus.innerHTML = `
                Replay: ${replayIndex + 1}/${memoryData.length}<br>
                <span style="font-size:10px;color:#aaa">${d.toLocaleTimeString()}</span><br>
                AKSI: <b>${snap.aksi.toFixed(3)}</b> | Res: <b>${snap.resonance.toFixed(3)}</b><br>
                Объектов: ${snap.objectsCount} | ${snap.topEvent ? snap.topEvent.label : "—"}
            `;
        }

        replayIndex++;
        if (replayIndex >= memoryData.length) stopReplay();
    }, 500);
}

function stopReplay() {
    isReplayingMemory = false;
    if (replayTimer) { clearInterval(replayTimer); replayTimer = null; }
    const replayStatus = document.getElementById("replay-status");
    if (replayStatus) replayStatus.textContent = "Replay завершён";
}

// Инициализация кнопки Replay
export function initReplayButton() {
    const btn = document.getElementById("replay-btn");
    if (btn) {
        btn.addEventListener("click", () => {
            if (isReplayingMemory) stopReplay();
            else startReplay();
        });
    }
}

// --- Семантический поиск ---

export function initSemanticSearch() {
    const searchBtn = document.getElementById("search-btn");
    const searchInput = document.getElementById("search-input");
    const searchResults = document.getElementById("search-results");

    if (!searchBtn || !searchInput || !searchResults) return;

    searchBtn.addEventListener("click", async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        searchResults.innerHTML = "<div style='color:#aaa;font-size:11px'>Поиск...</div>";

        try {
            const resp = await fetch(`/api/search-events?query=${encodeURIComponent(query)}`);
            const data = await resp.json();

            if (!data.results || data.results.length === 0) {
                searchResults.innerHTML = "<div style='color:#888;font-size:11px'>Ничего не найдено</div>";
                return;
            }

            searchResults.innerHTML = data.results.map(r => `
                <div class="search-result">
                    <span class="sr-type">${r.event.type}</span>
                    <span class="sr-label">${r.event.label || ""}</span>
                    <span class="sr-score">${(r.score * 100).toFixed(0)}%</span>
                </div>
            `).join("");
        } catch (e) {
            searchResults.innerHTML = "<div style='color:#f44;font-size:11px'>Ошибка поиска</div>";
        }
    });

    // Поиск по Enter
    searchInput.addEventListener("keydown", e => {
        if (e.key === "Enter") searchBtn.click();
    });
}

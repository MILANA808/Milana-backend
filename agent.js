// AKSI browser-safe agent bridge. No secrets are exposed here.
(() => {
  const API = 'https://milana-backend.replit.app';
  async function searchWeb(q) {
    const r = await fetch(`${API}/api/world/search?q=${encodeURIComponent(q)}`);
    if (!r.ok) throw new Error(`Web gateway HTTP ${r.status}`);
    return r.json();
  }
  async function capabilities() {
    const r = await fetch(`${API}/`);
    if (!r.ok) throw new Error(`Agent gateway HTTP ${r.status}`);
    return r.json();
  }
  window.AKSIAgent = Object.freeze({ API, searchWeb, capabilities });
})();

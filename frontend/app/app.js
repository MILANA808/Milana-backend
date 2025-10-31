const d = document;
const qs = (s)=>d.querySelector(s);

// Load config
const DEF_API = 'https://milana-backend.onrender.com';
let API_BASE = localStorage.getItem('AKSI_API_BASE') || DEF_API;
let API_KEY  = localStorage.getItem('AKSI_API_KEY')  || '';

qs('#apiBase').value = API_BASE;
qs('#apiKey').value  = API_KEY;

qs('#saveCfg').onclick = ()=>{
  API_BASE = (qs('#apiBase').value || DEF_API).replace(/\/$/,'');
  API_KEY  = qs('#apiKey').value || '';
  localStorage.setItem('AKSI_API_BASE', API_BASE);
  localStorage.setItem('AKSI_API_KEY',  API_KEY);
  ping();
};

async function request(path, method, body){
  const headers = { 'Content-Type': 'application/json' };
  if (API_KEY) headers['X-API-Key'] = API_KEY;
  const r = await fetch(API_BASE+path, { method, headers, body: body?JSON.stringify(body):undefined });
  if (!r.ok) throw new Error((await r.text())||('HTTP '+r.status));
  return await r.json();
}

async function ping(){
  const dot = qs('#status');
  dot.className = 'dot yellow';
  try{
    const res = await request('/health','GET');
    if (res && res.status === 'ok') { dot.className = 'dot green'; }
    else { dot.className = 'dot red'; }
  }catch(e){ dot.className = 'dot red'; }
}

qs('#eqsBtn').onclick = async ()=>{
  const out = qs('#eqsOut'); out.textContent = '…';
  try{
    const data = await request('/eqs/score','POST',{ text: qs('#eqsText').value.trim() });
    out.textContent = JSON.stringify(data,null,2);
    try{ speechSynthesis.speak(new SpeechSynthesisUtterance('EQS '+Math.round(data.score))); }catch(e){}
  }catch(e){ out.textContent = 'Ошибка: '+e.message; }
};

qs('#psiBtn').onclick = async ()=>{
  const out = qs('#psiOut'); out.textContent = '…';
  try{
    const data = await request('/psi/state','POST',{
      omega: parseFloat(qs('#omega').value),
      phi: parseFloat(qs('#phi').value),
      amplitude: parseFloat(qs('#amp').value)
    });
    out.textContent = JSON.stringify(data,null,2);
  }catch(e){ out.textContent = 'Ошибка: '+e.message; }
};

// Kick
ping();

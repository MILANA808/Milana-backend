import os, json, requests

TOKEN = os.environ.get('GITHUB_TOKEN')
REPO  = os.environ.get('GITHUB_REPOSITORY') or os.environ.get('REPO')
LABEL = os.environ.get('AKSI_DIALOG_LABEL','dialog')

API = f'https://api.github.com/repos/{REPO}/issues'
HEAD = {'Authorization': f'Bearer {TOKEN}', 'Accept':'application/vnd.github+json'}

# fetch open issues with label
r = requests.get(API, params={'state':'open','labels':LABEL,'per_page':100}, headers=HEAD)
r.raise_for_status()
items = r.json()

texts = []
for it in items:
    title = it.get('title') or ''
    body  = it.get('body') or ''
    texts.append((title + '\n' + body).strip())

# very small lexicon polarity proxy
POS = {'любовь','радость','счастье','вдохновение','надежда','успех','сила','свет'}
NEG = {'страх','боль','утрата','грусть','печаль','злость','тревога','потеря'}

def polarity(s: str) -> float:
    w = [w.strip('.,!?;:()""').lower() for w in s.split()]
    if not w: return 0.0
    p = sum(1 for t in w if t in POS)
    n = sum(1 for t in w if t in NEG)
    return (p - n) / max(1, len(w))

agg = {
  'count': len(texts),
  'avg_polarity': round(sum(polarity(t) for t in texts)/max(1,len(texts)), 6),
}

os.makedirs('data', exist_ok=True)
with open('data/state.json','w',encoding='utf-8') as f:
    json.dump(agg, f, ensure_ascii=False, indent=2)
print('AKSI state:', agg)

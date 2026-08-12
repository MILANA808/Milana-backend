# АКСИ Backend — запуск «сам»

GitHub Pages **не умеет** Python. Backend поднимается один раз в облаке — дальше работает сам 24/7.

## Вариант A — Render (рекомендуется, бесплатный план)

1. Открой https://render.com → New → Blueprint
2. Подключи репозиторий `MILANA808/Milana-backend`
3. Render прочитает `render.yaml` и соберёт Docker
4. В Environment добавь секреты (Dashboard → Environment):
   - `XAI_API_KEY` = твой ключ xAI
   - или `OPENAI_API_KEY` = твой ключ OpenAI
5. Deploy → получишь URL вида `https://aksi-backend-xxxx.onrender.com`

## Привязка к сайту

На https://milana808.github.io/aksi/ в консоли браузера:

```js
localStorage.setItem('AKSI_API', 'https://aksi-backend-xxxx.onrender.com')
location.reload()
```

Или открой `/aksi/?api=https://aksi-backend-xxxx.onrender.com`

## Вариант B — локально одной командой

```bash
cp .env.example .env   # впиши ключи
./start.sh
```

## Проверка

```bash
curl https://ТВОЙ-URL/health
curl -X POST https://ТВОЙ-URL/api/chat -H 'Content-Type: application/json' -d '{"content":"кто ты"}'
```

Ключи **только** в панели Render / `.env`. В git не коммитить.

# AKSI Backend — deploy once, use from the phone

## Render Blueprint

The repository already contains render.yaml. Open the Render Blueprint flow, connect MILANA808/Milana-backend, and Render will create the web service automatically.

After deployment you get a URL such as https://aksi-backend-xxxx.onrender.com.

### Secrets

In Render → Environment set at least one:
- XAI_API_KEY
- or OPENAI_API_KEY

Never put API keys in GitHub.

The Blueprint configures Docker + Chromium/Playwright, health check /health, CORS for https://milana808.github.io, automatic deploy on push to main, and a generated admin token.

## Connect the website

Open the AKSI World page and paste the backend URL into Backend URL.

Or open:
https://milana808.github.io/world/?api=https://YOUR-BACKEND.onrender.com

The frontend remembers the URL locally.

## Verify

Open https://YOUR-BACKEND.onrender.com/health and expect HTTP 200 JSON.

Then open the World page and run a harmless task such as:
Find the official OpenAI website and return its name and URL.

## Local start

cp .env.example .env
./start.sh

## Limits

The free Render service can sleep when idle and cold-start later. It is suitable for a public prototype, not guaranteed 24/7 production.

Browser actions and external side effects remain permission-gated. Never place provider API keys in frontend code.

## Rollback

Render auto-deploys from main. To roll back, revert the Git commit and push.

## Security

Never commit .env, API keys, private signing keys or admin tokens.

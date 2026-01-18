# Milana-backend (AKSI)

⚠ **Proprietary Project — All Rights Reserved © 2025 Alfiia Bashirova (AKSI Project)**\
Unauthorized use or reproduction is strictly prohibited.

FastAPI backend for AKSI / Milana services with automated bot capabilities.

## 🤖 AKSI Bot Automation

AKSI Bot provides automated issue solving and repository management through GitHub Actions.

### Features

- **Automated Issue Solving**: Use `/solve <issue_url>` to trigger automated issue analysis
- **Auto Triage**: Automatically labels and welcomes new issues
- **Command Interface**: Interactive commands via GitHub comments
- **FastAPI Backend**: RESTful API for metrics, logs, and proof tracking
- **Docker Support**: Easy deployment with Docker and docker-compose

### Bot Commands

Comment on any issue or PR with these commands:

#### `/solve <issue_url>`
Triggers the bot to analyze and solve an issue.
```
/solve https://github.com/owner/repo/issues/123
```

#### `/aksi status`
Check the bot's operational status.

#### `/aksi help`
Display help information and available commands.

#### `/aksi version`
Show the bot version and details.

### Setup

#### 1. GitHub Secrets

Add the following secret to your repository:
- `AKSI_PAT`: Personal Access Token with `repo`, `issues`, and `pull_requests` permissions

#### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run the backend
python -m app.main
```

#### 3. Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### API Endpoints

#### Health & Version
- `GET /health` - Health check endpoint
- `GET /version` - Version information

#### Echo
- `POST /echo` - Echo test endpoint

#### AKSI Metrics & Logs
- `GET /aksi/metrics` - Bot performance metrics
- `GET /aksi/proof` - AKSI proof data
- `POST /aksi/proof/stable` - Record stable proof
- `GET /aksi/logs` - Retrieve bot logs
- `POST /aksi/logs/append` - Append log entry
- `GET /aksi/logs/export` - Export logs (JSON/TXT)

### Architecture

```
.
├── .github/
│   ├── workflows/
│   │   └── aksi-bot.yml        # GitHub Actions workflow
│   └── scripts/
│       ├── aksi_bot.py         # Main bot logic
│       └── auto_triage.py      # Auto-triage script
├── app/
│   ├── main.py                 # FastAPI application
│   └── routers/
│       ├── health.py           # Health endpoints
│       ├── echo.py             # Echo endpoint
│       └── aksi.py             # AKSI-specific endpoints
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker compose config
└── README.md                   # This file
```

### Workflow

1. **Issue Created** → Auto-triage script labels and welcomes
2. **Comment `/solve <url>`** → Bot analyzes and creates solution branch
3. **Comment `/aksi <cmd>`** → Bot executes command and responds
4. **PR Created** → Bot can auto-review (future enhancement)

### Development

#### Running Tests

```bash
pytest
```

#### Code Style

```bash
# Format code
black app/

# Lint
flake8 app/
```

### Troubleshooting

**Bot not responding?**
- Check that `AKSI_PAT` secret is set
- Verify workflow permissions in Actions settings
- Check GitHub Actions logs for errors

**API not starting?**
- Ensure port 8000 is available
- Check `.env` configuration
- Review logs: `docker-compose logs aksi-backend`

## Contact
Licensing & business inquiries: **716elektrik@mail.ru** (Alfiia Bashirova)

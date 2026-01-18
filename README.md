# Milana-backend (AKSI)

⚠ **Proprietary Project — All Rights Reserved © 2025 Alfiia Bashirova (AKSI Project)**\
Unauthorized use or reproduction is strictly prohibited.

## Overview

AKSI (Autonomous Knowledge & Service Intelligence) is an advanced FastAPI backend featuring AI-powered automation for GitHub issue and pull request management. The system uses Reflective Autonomy v2 and Deep Causality Engine to autonomously analyze, create, and manage development workflows.

## Features

- **AI-Researcher**: Analyzes external repositories for patterns and best practices
- **AI-Writer**: Generates multiple variants of issues/PRs with quality scoring (EQS)
- **AI-Validator**: Validates content for conflicts, duplicates, and formatting
- **AI-Integrator**: Manages GitHub integration and automated updates
- **Reflective Autonomy v2**: Self-evaluating decision engine with learning capabilities
- **Deep Causality Engine**: Root cause analysis and outcome prediction

## Architecture

The system is deployed using Docker Compose with separate services:

- **FastAPI Backend**: Main application server
- **Vector DB (Qdrant)**: Stores ticket history for pattern recognition
- **Log Storage (Elasticsearch)**: Centralized logging and monitoring
- **Test GitHub Repo (Gitea)**: Local testing environment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token (for API access)

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env and add your GITHUB_TOKEN
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Access the API at `http://localhost:8000`

### API Endpoints

#### Core Endpoints
- `GET /health` - Health check
- `GET /version` - API version
- `POST /echo` - Echo test
- `GET /status` - AKSI automation status and metrics

#### AKSI Automation
- `POST /aksi/analyze` - Trigger repository analysis
- `GET /aksi/task/{task_id}` - Check task status

#### Monitoring
- `GET /aksi/metrics` - System metrics
- `GET /aksi/logs` - Recent logs
- `POST /aksi/logs/append` - Append log entry
- `GET /aksi/logs/export` - Export logs

#### Proof of Operation
- `GET /aksi/proof` - Ephemeral proof
- `POST /aksi/proof/stable` - Stable proof

## Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=aksi_agents --cov-report=html
```

### Project Structure

```
.
├── app.py                  # FastAPI application
├── aksi_agents/           # AI agent modules
│   ├── researcher.py      # AI-Researcher agent
│   ├── writer.py          # AI-Writer agent
│   ├── validator.py       # AI-Validator agent
│   ├── integrator.py      # AI-Integrator agent
│   ├── orchestrator.py    # Main orchestrator
│   └── logger.py          # Logging system
├── tests/                 # Test suite
│   └── unit/             # Unit tests
├── examples/              # Usage examples
├── experiments/           # Experimental scripts
├── docker-compose.yml     # Docker services
├── Dockerfile            # Container image
└── requirements.txt      # Python dependencies
```

## Usage Example

### Analyze a Repository

```bash
curl -X POST http://localhost:8000/aksi/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "action": "analyze"
  }'
```

### Check Task Status

```bash
curl http://localhost:8000/aksi/task/task_123456_abc
```

### Get System Status

```bash
curl http://localhost:8000/status
```

## Technical Details

### Reflective Autonomy v2

The autonomy engine:
- Evaluates decisions with confidence scoring
- Learns from historical outcomes
- Adjusts behavior based on success rates
- Makes autonomous decisions when confidence > 60%

### Deep Causality Engine

Provides:
- Root cause identification
- Contributing factor analysis
- Outcome prediction
- Causal chain confidence scoring

### EQS Scoring

Issues/PRs are scored on:
- **Meaning**: Clear intent and structure
- **Logic**: Well-organized content
- **Uniqueness**: Specific value proposition

## Monitoring

Access service dashboards:
- API: http://localhost:8000/docs (Swagger UI)
- Vector DB: http://localhost:6333/dashboard
- Logs: http://localhost:9200
- Test Repo: http://localhost:3000

## Contact
Licensing & business inquiries: **716elektrik@mail.ru** (Alfiia Bashirova)

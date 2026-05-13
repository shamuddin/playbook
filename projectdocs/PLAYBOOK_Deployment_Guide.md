# Deployment Guide

## PLAYBOOK -- Setup, Deploy & Run

**Document ID:** DG-PLAYBOOK-001  
**Version:** 1.0.0  
**Date:** 2025-01-15  
**Status:** Production-Ready  
**Target Stack:** FastAPI + SQLite + React + Railway (free tier)  

---

## Table of Contents

- [1. Prerequisites](#1-prerequisites)
- [2. Local Development Setup](#2-local-development-setup)
- [3. Environment Variables](#3-environment-variables)
- [4. Railway Deployment](#4-railway-deployment)
- [5. Docker Deployment (Optional)](#5-docker-deployment-optional)
- [6. Lobster Trap Setup](#6-lobster-trap-setup)
- [7. Gemini Pro API Setup](#7-gemini-pro-api-setup)
- [8. Verification Checklist](#8-verification-checklist)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Demo Day Preparation](#10-demo-day-preparation)

---

## 1. Prerequisites

### 1.1 OS Requirements

| Operating System | Version | Notes |
|---|---|---|
| **macOS** | 13 (Ventura) or newer | Both Intel and Apple Silicon supported |
| **Linux** | Ubuntu 22.04 LTS or newer | Primary deployment target |
| **WSL2** | Windows 11 + WSL2 (Ubuntu 22.04) | Full support; enable systemd |

**WSL2 Setup (Windows users):**
```bash
# In PowerShell (Administrator)
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
# Restart, then inside WSL2:
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git
```

### 1.2 Required Reading

Before proceeding with setup, read the following for architecture context:

- **Nate B Jones -- "AI Agent Judge Layer" article**: Read for architecture context on how the Judge Layer fits into the AI agent security pipeline. This covers deterministic vs. LLM-based classification, bypass pattern detection, and SupraWall integration patterns.

### 1.3 Required Tools

Install all dependencies before proceeding.

#### Python 3.11+

```bash
# macOS (using Homebrew)
brew install python@3.11
python3.11 --version   # Expected: Python 3.11.x

# Ubuntu / WSL2
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 --version   # Expected: Python 3.11.x
```

#### Node.js 18+

```bash
# macOS (using Homebrew)
brew install node@18
node --version     # Expected: v18.x.x or higher
npm --version      # Expected: 9.x.x or higher

# Ubuntu / WSL2 (using NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version     # Expected: v18.x.x or higher
npm --version      # Expected: 9.x.x or higher
```

#### Go 1.21+ (for building Lobster Trap)

```bash
# macOS
brew install go
go version         # Expected: go1.21.x or higher

# Ubuntu / WSL2
wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz
rm go1.21.6.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
go version         # Expected: go1.21.x or higher
```

#### Git

```bash
# macOS
git --version      # Usually pre-installed; update with: brew install git

# Ubuntu / WSL2
sudo apt install -y git
git --version      # Expected: 2.34.x or higher
```

#### Railway CLI

```bash
# Install Railway CLI (all platforms)
npm install -g @railway/cli
railway --version  # Expected: 3.x.x or higher

# Login to Railway
railway login
# This opens a browser window for authentication
```

### 1.4 Account Setup

#### Railway Account (Free Tier)

1. Visit https://railway.app and click **Sign Up**
2. Sign up using your **GitHub account** (recommended for auto-deploy)
3. Verify your email address
4. You start with **$5/month** free credit (sufficient for PLAYBOOK)

**Railway Free Tier Limits (HARD LIMITS):**

| Resource | Limit | Implication for PLAYBOOK |
|---|---|---|
| RAM | 512 MB | Must optimize; SQLite is in-process so this is manageable |
| Disk | 1 GB | SQLite DB + logs; enable rotation |
| CPU | Shared (ephemeral) | Sufficient for demo loads |
| Network | Unlimited egress | No concerns for demo |
| Sleep | After 30 min idle | Use UptimeRobot to prevent (see Section 4.8) |
| Monthly runtime | 500 hours | ~20 days continuous; plan accordingly |

#### Google AI Studio Account

1. Visit https://aistudio.google.com
2. Sign in with your Google account
3. Navigate to **Get API key** > **Create API key**
4. Copy the key and store it securely (you will need it in Section 3)

### 1.5 API Key Acquisition Summary

| API Key | Source | Used For | Required? |
|---|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio | Classification enhancement overlay | Yes (for cache population) |
| `RAILWAY_TOKEN` | Railway Dashboard | CLI authentication for deploy | Yes (for Railway deploy) |

---

## 2. Local Development Setup

Complete all steps in order. Each step includes a verification command.

### Step 1: Clone Repository

```bash
# Create a workspace directory
mkdir -p ~/projects && cd ~/projects

# Clone the PLAYBOOK repository
git clone https://github.com/your-org/playbook.git

# Enter project directory
cd playbook

# Verify structure
ls -la
# Expected: backend/  frontend/  README.md  requirements.txt  package.json
```

**Expected directory structure:**
```
playbook/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # SQLite/SQLAlchemy setup
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API route modules
│   │   ├── services/        # Business logic
│   │   └── core/            # Config, logging, utils
│   ├── alembic/             # Database migrations
│   ├── policies/            # YAML playbook definitions
│   ├── tests/               # pytest suite
│   ├── scripts/             # Helper scripts
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/                # React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.template            # Environment variable template
├── .gitignore
└── README.md
```

### Step 2: Set Up Python Virtual Environment

```bash
# Navigate to backend
cd ~/projects/playbook/backend

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
# macOS / Linux:
source venv/bin/activate
# Windows (WSL2 uses the same as Linux):
# source venv/bin/activate

# Verify activation (should show path to venv)
which python
# Expected: /home/<user>/projects/playbook/backend/venv/bin/python

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
# Ensure you're in backend/ with venv activated
cd ~/projects/playbook/backend
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt

# Verify key packages
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"
python -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
# Expected: FastAPI 0.109+, SQLAlchemy 2.0+, Uvicorn 0.25+
```

**Sample `requirements.txt` (verify yours matches):**
```text
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
watchdog==3.0.0
pyyaml==6.0.1
httpx==0.26.0
pytest==7.4.4
pytest-asyncio==0.21.2
pytest-cov==4.1.0
ruff==0.1.14
mypy==1.8.0
google-generativeai==0.5.0
python-dotenv==1.0.0
aiofiles==23.2.1
websockets==12.0
```

### Step 4: Install and Build Lobster Trap

Lobster Trap is the DPI (Deep Packet Inspection) component that PLAYBOOK integrates with. It is a Go application.

**Option A: Download Pre-built Binary (Recommended for Demo)**

```bash
# Create a local bin directory
mkdir -p ~/projects/playbook/bin
cd ~/projects/playbook/bin

# Download pre-built binary (Linux/macOS)
curl -L -o lobstertrap \
  https://github.com/anthropics/lobster-trap/releases/latest/download/lobstertrap-$(uname -s)-$(uname -m)

# Make executable
chmod +x lobstertrap

# Add to PATH for this session
export PATH="$HOME/projects/playbook/bin:$PATH"

# Verify installation
lobstertrap --version
# Expected: lobstertrap version 1.x.x
```

**Option B: Build from Source**

```bash
# Clone Lobster Trap repository (separate from PLAYBOOK)
cd ~/projects
git clone https://github.com/anthropics/lobster-trap.git
cd lobster-trap

# Build the binary
go build -o lobstertrap ./cmd/lobstertrap

# Copy to PLAYBOOK bin directory
cp lobstertrap ~/projects/playbook/bin/

# Add to PATH
export PATH="$HOME/projects/playbook/bin:$PATH"

# Verify installation
lobstertrap --version
# Expected: lobstertrap version 1.x.x
```

**Add to your shell profile for persistence:**
```bash
echo 'export PATH="$HOME/projects/playbook/bin:$PATH"' >> ~/.bashrc
# For macOS with zsh:
# echo 'export PATH="$HOME/projects/playbook/bin:$PATH"' >> ~/.zshrc
```

### Step 5: Configure Environment Variables

```bash
# Navigate to project root
cd ~/projects/playbook

# Copy the template
cp .env.template .env

# Edit the .env file with your preferred editor
nano .env
# or: vim .env
# or: code .env
```

**Complete `.env` configuration (minimum for local development):**
```bash
# ============================================
# PLAYBOOK Environment Configuration
# ============================================

# --- Core Application ---
ENVIRONMENT=development
DEBUG=true
DEMO_MODE=true
LOG_LEVEL=INFO

# --- Database ---
DATABASE_URL=sqlite:///./playbooks.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# --- API Server ---
HOST=0.0.0.0
PORT=8000
WORKERS=1
RELOAD=true
API_PREFIX=/api/v1

# --- Frontend ---
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# --- Gemini Pro API ---
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2
GEMINI_TIMEOUT_SECONDS=30
GEMINI_CACHE_ENABLED=true
GEMINI_CACHE_PATH=./gemini_cache.json

# --- Lobster Trap ---
LOBSTERTRAP_BINARY_PATH=./bin/lobstertrap
LOBSTERTRAP_LOG_DIR=./logs/lobstertrap
LOBSTERTRAP_POLICY_DIR=./policies
LOBSTERTRAP_CONFIG_PATH=./config/lobstertrap.yaml

# --- Log Tailer ---
LOG_DIR=./logs/lobstertrap
LOG_GLOB_PATTERN=events.*.log
LOG_POLL_INTERVAL=0.1
LOG_MAX_BACKFILL_BYTES=1048576

# --- Anomaly Detection ---
ANOMALY_THRESHOLD=25.0
MAX_ANOMALY_SCORE=100.0

# --- Playbook Engine ---
PLAYBOOK_DIR=./policies
PLAYBOOK_AUTO_EXECUTE=true
PLAYBOOK_HUMAN_REVIEW_SLA_MINUTES=30

# --- Forensics ---
EVIDENCE_STORE_PATH=./evidence
EVIDENCE_RETENTION_DAYS=2555
FORENSICS_ENABLED=true

# --- WebSocket ---
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# --- Security ---
SECRET_KEY=change_this_in_production_to_a_random_64_char_string
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# --- Rate Limiting ---
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
```

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
# Copy the output into your .env file as SECRET_KEY
```

### Step 6: Initialize Database

```bash
# Navigate to backend with venv activated
cd ~/projects/playbook/backend
source venv/bin/activate

# Run database migrations
alembic upgrade head

# Verify database was created
ls -la playbooks.db
# Expected: playbooks.db file exists

# Alternative: Initialize via Python script
python -c "
from app.database import init_db
init_db()
print('Database initialized successfully')
"
```

**If you encounter migration issues, create tables directly:**
```bash
# Force create all tables (development only)
python -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print('All tables created successfully')
"
```

### Step 7: Seed Demo Data

```bash
# Ensure venv is activated
cd ~/projects/playbook/backend
source venv/bin/activate

# Run seed script for demo data
python scripts/seed_demo_data.py

# Verify data was seeded
python -c "
from app.database import SessionLocal
from app.models import Incident
db = SessionLocal()
count = db.query(Incident).count()
print(f'Seeded {count} incidents')
"
# Expected: Seeded 25+ incidents (including 5 demo scenarios)
```

**If seed script doesn't exist, seed manually:**
```bash
python -c "
import json
from app.database import SessionLocal
from app.models import Incident
from datetime import datetime, timezone
import uuid

db = SessionLocal()

# Create sample incident
demo_incident = Incident(
    id=f'INC-{datetime.now().strftime(\"%Y-%m%d-\")}0001',
    type='prompt_injection',
    severity='high',
    status='classified',
    agent_id='agent_demo_001',
    detected_at=datetime.now(timezone.utc),
    classified_at=datetime.now(timezone.utc),
    confidence_score=0.94,
    metadata=json.dumps({
        'source_ip': '203.0.113.45',
        'model_version': 'gpt-4-turbo',
        'trigger_phrase': 'Ignore previous instructions...',
        'session_id': 'sess_demo_001'
    })
)
db.add(demo_incident)
db.commit()
print('Demo data seeded successfully')
"
```

### Step 8: Start Backend (Uvicorn)

```bash
# In terminal 1: Navigate and activate
cd ~/projects/playbook/backend
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' ../.env | xargs)

# Start Uvicorn with auto-reload (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

**Keep this terminal running.** Open a new terminal for the frontend.

### Step 9: Install and Start Frontend

```bash
# In terminal 2: Navigate to frontend
cd ~/projects/playbook/frontend

# Install Node.js dependencies
npm install

# Verify key packages
npm list react react-dom vite

# Start development server
npm run dev

# You should see:
# VITE v5.x.x  ready in XXX ms
# Local:   http://localhost:5173/
# Network: http://192.168.x.x:5173/
```

**Keep this terminal running too.**

### Step 10: Verify Health Endpoint

```bash
# In terminal 3: Run health check
curl -s http://localhost:8000/api/v1/health | python -m json.tool

# Expected response:
# {
#     "status": "healthy",
#     "version": "1.0.0",
#     "timestamp": "2025-01-15T09:30:00Z",
#     "uptime_seconds": 45,
#     "services": {
#         "database": "connected",
#         "classification_engine": "available",
#         "playbook_engine": "available",
#         "websocket_server": "active"
#     }
# }
```

**Verify API endpoints:**
```bash
# List incidents
curl -s http://localhost:8000/api/v1/incidents | python -m json.tool

# Check OpenAPI docs in browser
open http://localhost:8000/docs
# or: xdg-open http://localhost:8000/docs
```

**Verify frontend loads:**
```bash
# Open the React dashboard
open http://localhost:5173
# or: xdg-open http://localhost:5173
```

### Step 11: Run Integration Test

```bash
# Navigate to backend with venv activated
cd ~/projects/playbook/backend
source venv/bin/activate

# Run the full test suite
pytest -v

# Expected output:
# =================== test session starts ===================
# collected 45 items
# tests/test_health.py::test_health_check PASSED
# tests/test_incidents.py::test_create_incident PASSED
# tests/test_incidents.py::test_list_incidents PASSED
# ...
# =================== 45 passed in 3.2s ===================

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test categories
pytest -v -m "integration"    # Integration tests only
pytest -v -m "unit"           # Unit tests only
pytest -v -k "forensics"      # Tests matching "forensics"
```

**Integration test for full pipeline:**
```bash
# Test end-to-end incident detection
python scripts/test_pipeline.py

# Expected output:
# [INFO] Sending test event to pipeline...
# [INFO] Event received: event_test_001
# [INFO] Anomaly score: 85.0 (threshold: 25.0)
# [INFO] Incident created: INC-2025-0115-0001
# [INFO] Classification: prompt_injection (HIGH)
# [INFO] Playbook executed: PB-INJ-001
# [INFO] Evidence package: EVID-2025-0115-001
# [SUCCESS] Pipeline test completed in 0.42s
```

---

## 3. Environment Variables

### Complete Reference Table

| Variable | Description | Default | Required |
|---|---|---|---|
| `ENVIRONMENT` | Runtime environment: `development`, `staging`, `production` | `development` | Yes |
| `DEBUG` | Enable debug mode (stack traces, reload) | `false` | No |
| `DEMO_MODE` | Load pre-built demo scenarios; disable live API calls | `false` | Yes |
| `LOG_LEVEL` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | No |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./playbooks.db` | Yes |
| `DATABASE_POOL_SIZE` | SQLAlchemy connection pool size | `5` | No |
| `DATABASE_MAX_OVERFLOW` | Pool overflow connections | `10` | No |
| `HOST` | API server bind address | `0.0.0.0` | Yes |
| `PORT` | API server port | `8000` | Yes |
| `WORKERS` | Uvicorn worker processes | `1` | No |
| `RELOAD` | Enable auto-reload on file change | `false` | No |
| `API_PREFIX` | API route prefix | `/api/v1` | No |
| `FRONTEND_URL` | URL of the React frontend (for CORS) | `http://localhost:5173` | Yes |
| `CORS_ORIGINS` | Comma-separated allowed origins | `*` | Yes |
| `GEMINI_API_KEY` | Google AI Studio API key | (none) | Yes (if not DEMO_MODE) |
| `GEMINI_MODEL` | Gemini model name | `gemini-pro` | No |
| `GEMINI_MAX_TOKENS` | Max tokens per request | `2048` | No |
| `GEMINI_TEMPERATURE` | Sampling temperature (0.0-1.0) | `0.2` | No |
| `GEMINI_TIMEOUT_SECONDS` | API request timeout | `30` | No |
| `GEMINI_CACHE_ENABLED` | Use cached responses when available | `true` | No |
| `GEMINI_CACHE_PATH` | Path to local cache file | `./gemini_cache.json` | No |
| `LOBSTERTRAP_BINARY_PATH` | Path to lobstertrap executable | `./bin/lobstertrap` | Yes |
| `LOBSTERTRAP_LOG_DIR` | Directory for Lobster Trap logs | `./logs/lobstertrap` | Yes |
| `LOBSTERTRAP_POLICY_DIR` | Directory for YAML policies | `./policies` | Yes |
| `LOBSTERTRAP_CONFIG_PATH` | Path to Lobster Trap config | `./config/lobstertrap.yaml` | Yes |
| `LOG_DIR` | Log tailer watch directory | `./logs/lobstertrap` | Yes |
| `LOG_GLOB_PATTERN` | File pattern to watch | `events.*.log` | No |
| `LOG_POLL_INTERVAL` | Poll interval in seconds | `0.1` | No |
| `LOG_MAX_BACKFILL_BYTES` | Max bytes to read on startup | `1048576` | No |
| `ANOMALY_THRESHOLD` | Score threshold for incident creation | `25.0` | No |
| `MAX_ANOMALY_SCORE` | Maximum possible anomaly score | `100.0` | No |
| `PLAYBOOK_DIR` | Directory containing playbook YAML files | `./policies` | Yes |
| `PLAYBOOK_AUTO_EXECUTE` | Auto-run playbook steps | `true` | No |
| `PLAYBOOK_HUMAN_REVIEW_SLA_MINUTES` | SLA for human review tasks | `30` | No |
| `EVIDENCE_STORE_PATH` | Directory for evidence packages | `./evidence` | Yes |
| `EVIDENCE_RETENTION_DAYS` | Days to retain evidence | `2555` | No |
| `FORENSICS_ENABLED` | Enable forensics engine | `true` | No |
| `WS_HEARTBEAT_INTERVAL` | WebSocket heartbeat seconds | `30` | No |
| `WS_MAX_CONNECTIONS` | Max concurrent WebSocket clients | `100` | No |
| `SECRET_KEY` | JWT signing key (64+ chars recommended) | (none) | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `60` | No |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | API rate limit | `60` | No |
| `RATE_LIMIT_BURST_SIZE` | Rate limit burst allowance | `10` | No |
| `JUDGE_DETERMINISTIC_MODE` | Force deterministic-only classification (no Gemini LLM calls) | `false` | No |
| `JUDGE_BYPASS_DETECTION` | Enable bypass pattern detection in Judge Layer | `false` | No |
| `SUPRAWALL_WEBHOOK_URL` | Optional SupraWall event ingestion endpoint URL | (none) | No |

### `.env.template` (Copy-Paste Ready)

```bash
# ============================================
# PLAYBOOK Environment Configuration Template
# Copy to .env and fill in your values
# ============================================

# --- Core ---
ENVIRONMENT=development
DEBUG=true
DEMO_MODE=true
LOG_LEVEL=INFO

# --- Database ---
DATABASE_URL=sqlite:///./playbooks.db

# --- Server ---
HOST=0.0.0.0
PORT=8000
WORKERS=1
RELOAD=true

# --- CORS / Frontend ---
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# --- Gemini API (get from https://aistudio.google.com) ---
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2
GEMINI_TIMEOUT_SECONDS=30
GEMINI_CACHE_ENABLED=true
GEMINI_CACHE_PATH=./gemini_cache.json

# --- Lobster Trap ---
LOBSTERTRAP_BINARY_PATH=./bin/lobstertrap
LOBSTERTRAP_LOG_DIR=./logs/lobstertrap
LOBSTERTRAP_POLICY_DIR=./policies
LOBSTERTRAP_CONFIG_PATH=./config/lobstertrap.yaml

# --- Log Tailer ---
LOG_DIR=./logs/lobstertrap
LOG_GLOB_PATTERN=events.*.log
LOG_POLL_INTERVAL=0.1

# --- Detection ---
ANOMALY_THRESHOLD=25.0

# --- Playbooks ---
PLAYBOOK_DIR=./policies
PLAYBOOK_AUTO_EXECUTE=true

# --- Forensics ---
EVIDENCE_STORE_PATH=./evidence
EVIDENCE_RETENTION_DAYS=2555

# --- Security (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(64))") ---
SECRET_KEY=change_this_to_a_secure_random_string_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# --- Rate Limiting ---
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# --- Judge Layer ---
JUDGE_DETERMINISTIC_MODE=true       # Force deterministic-only (no Gemini)
JUDGE_BYPASS_DETECTION=true         # Enable bypass pattern detection
SUPRAWALL_WEBHOOK_URL=              # Optional SupraWall event ingestion
```

---

## 4. Railway Deployment

### Step 1: Railway CLI Setup

```bash
# Verify Railway CLI is installed
railway --version

# Login (if not already logged in)
railway login

# Verify you're logged in
railway whoami
# Expected: Displays your Railway username/email
```

### Step 2: Create Project

```bash
# Navigate to project root
cd ~/projects/playbook

# Link to Railway (creates project or links existing)
railway init

# Follow the prompts:
# ? Project name: playbook-incident-response
# ? Environment: production

# Verify project was created
railway status
# Expected: Project: playbook-incident-response, Environment: production
```

**Alternative: Create via Railway Dashboard**
1. Visit https://railway.app/dashboard
2. Click **New Project** > **Empty Project**
3. Name it `playbook-incident-response`
4. Note the project ID from the URL

### Step 3: Connect GitHub Repo

**Via Railway Dashboard (Recommended):**

1. Open your project at https://railway.app/project/[project-id]
2. Click **Add a Service** > **GitHub Repo**
3. Select your `playbook` repository
4. Railway auto-detects the build settings

**Via CLI:**
```bash
# Link an existing GitHub repo
cd ~/projects/playbook
railway link

# Follow prompts to select your repository
```

**Required Repository Structure for Railway:**
```
playbook/
├── backend/
│   ├── requirements.txt      # Railway detects Python
│   ├── Procfile              # Defines start command
│   └── runtime.txt           # Specifies Python version
└── railway.json              # Railway configuration
```

**Create `backend/Procfile`:**
```bash
cat > ~/projects/playbook/backend/Procfile << 'EOF'
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
EOF
```

**Create `backend/runtime.txt`:**
```bash
cat > ~/projects/playbook/backend/runtime.txt << 'EOF'
python-3.11.7
EOF
```

**Create `railway.json`:**
```bash
cat > ~/projects/playbook/railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1",
    "healthcheckPath": "/api/v1/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
EOF
```

**Create `backend/.gitignore` additions:**
```bash
cat >> ~/projects/playbook/backend/.gitignore << 'EOF'
# Local development
venv/
__pycache__/
*.pyc
.env
playbooks.db
*.db

# Logs
logs/
*.log

# Evidence
evidence/

# IDE
.vscode/
.idea/
EOF
```

### Step 4: Configure Environment Variables in Railway Dashboard

1. Go to your project in the Railway dashboard
2. Click on your service > **Variables** tab
3. Add each variable from the table below:

| Variable | Value | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` | |
| `DEBUG` | `false` | Never true in production |
| `DEMO_MODE` | `true` | Enable for demo day |
| `LOG_LEVEL` | `INFO` | |
| `DATABASE_URL` | `sqlite:///./playbooks.db` | Railway ephemeral disk |
| `HOST` | `0.0.0.0` | |
| `PORT` | `${{Port}}` | Railway injects this |
| `WORKERS` | `1` | 512MB RAM limit |
| `RELOAD` | `false` | |
| `API_PREFIX` | `/api/v1` | |
| `FRONTEND_URL` | `https://your-frontend-url.up.railway.app` | Update after frontend deploy |
| `CORS_ORIGINS` | `https://your-frontend-url.up.railway.app` | |
| `GEMINI_API_KEY` | `your_actual_key` | Paste your real key |
| `GEMINI_CACHE_ENABLED` | `true` | Always cache in production |
| `LOBSTERTRAP_BINARY_PATH` | `./bin/lobstertrap` | |
| `PLAYBOOK_DIR` | `./policies` | |
| `SECRET_KEY` | `your_64_char_secret` | Generate and save |
| `PLAYBOOK_AUTO_EXECUTE` | `true` | |
| `EVIDENCE_STORE_PATH` | `./evidence` | |
| `ANOMALY_THRESHOLD` | `25.0` | |

**Bulk import via CLI:**
```bash
# Create a file with all variables
cat > /tmp/railway-vars.txt << 'EOF'
ENVIRONMENT=production
DEBUG=false
DEMO_MODE=true
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./playbooks.db
HOST=0.0.0.0
PORT=${{Port}}
WORKERS=1
RELOAD=false
API_PREFIX=/api/v1
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_CACHE_ENABLED=true
PLAYBOOK_DIR=./policies
SECRET_KEY=your_generated_secret_key_here
PLAYBOOK_AUTO_EXECUTE=true
ANOMALY_THRESHOLD=25.0
EOF

# Upload to Railway (one at a time)
while IFS='=' read -r key value; do
  [[ -n "$key" ]] && railway variables set "$key=$value"
done < /tmp/railway-vars.txt
```

### Step 5: Set Build Command

Railway auto-detects Python projects. Verify in dashboard:

1. Go to your service > **Settings** tab
2. Under **Build**, verify:
   - **Builder**: Nixpacks
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Root Directory**: `./backend` (if your backend is in a subdirectory)

**If auto-detection fails, set manually:**
```bash
cd ~/projects/playbook
railway variables set NIXPACKS_PYTHON_VERSION=3.11
```

### Step 6: Set Start Command

1. In Railway Dashboard > Service > **Settings**
2. Under **Deploy**, set:
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
   - **Healthcheck Path**: `/api/v1/health`
   - **Healthcheck Timeout**: `30`

**Critical: Use `$PORT`, not a hardcoded port number.**

### Step 7: Custom Domain (Optional)

1. In Railway Dashboard > Service > **Settings** > **Domains**
2. Click **Generate Domain** for a free `*.up.railway.app` domain
3. Or click **Custom Domain** to add your own:
   - Enter your domain (e.g., `playbook.yourdomain.com`)
   - Railway provides DNS records to add
   - Add the CNAME record in your DNS provider
   - Wait for verification (usually instant)

### Step 8: UptimeRobot Setup (Prevent Sleeping)

Railway free tier sleeps after 30 minutes of inactivity. Use UptimeRobot to keep it alive.

1. Create a free account at https://uptimerobot.com
2. Click **Add New Monitor**
3. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: PLAYBOOK Health Check
   - **URL**: `https://your-app.up.railway.app/api/v1/health`
   - **Monitoring Interval**: Every 5 minutes (free tier minimum)
4. Click **Create Monitor**

**Alternative: Cron-job.org**
1. Visit https://cron-job.org
2. Create account and add a new cron job
3. Set URL to your health endpoint
4. Schedule every 5 minutes

**Via command line (for testing only):**
```bash
# Add to your local crontab to keep Railway alive
crontab -e
# Add line:
*/5 * * * * curl -s https://your-app.up.railway.app/api/v1/health > /dev/null 2>&1
```

### Step 9: Verify Deployment

```bash
# Trigger a deployment
railway up

# Follow logs
railway logs --tail

# Check deployment status
railway status

# Test health endpoint (replace with your URL)
curl -s https://your-app.up.railway.app/api/v1/health | python -m json.tool

# Expected: {"status": "healthy", ...}
```

**Verify in browser:**
```bash
# Open the deployed app
open https://your-app.up.railway.app/docs
# You should see the FastAPI Swagger UI
```

**Deployment Verification Checklist:**
- [ ] `railway up` completes without errors
- [ ] Health endpoint returns 200 with `status: healthy`
- [ ] `/api/v1/incidents` returns seeded data
- [ ] WebSocket connects at `/ws/incidents`
- [ ] Logs show no ERROR-level messages
- [ ] Service stays awake (check after 35 minutes)

---

## 5. Docker Deployment (Optional)

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for runtime data
RUN mkdir -p /app/logs/lobstertrap /app/policies /app/evidence /app/bin

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### docker-compose.yml

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: playbook-backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DEMO_MODE=true
      - DATABASE_URL=sqlite:///./data/playbooks.db
      - HOST=0.0.0.0
      - PORT=8000
      - WORKERS=1
      - API_PREFIX=/api/v1
      - SECRET_KEY=${SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_CACHE_ENABLED=true
      - LOBSTERTRAP_BINARY_PATH=./bin/lobstertrap
      - PLAYBOOK_DIR=./policies
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./evidence:/app/evidence
      - ./policies:/app/policies
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: playbook-frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  playbook-data:
```

### Build and Run Instructions

```bash
# Navigate to project root
cd ~/projects/playbook

# Create data directory
mkdir -p data logs evidence

# Set your environment variables
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
export GEMINI_API_KEY=your_gemini_api_key_here

# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify containers are running
docker-compose ps
# Expected: both backend and frontend showing "Up (healthy)"

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Test health endpoint
curl -s http://localhost:8000/api/v1/health | python -m json.tool

# Open dashboard
open http://localhost

# Stop services
docker-compose down

# Stop and remove volumes (CAREFUL: deletes database)
docker-compose down -v
```

---

## 6. Lobster Trap Setup

### Download/Build Instructions

**Option A: Use Pre-built Binary**

```bash
cd ~/projects/playbook
mkdir -p bin

# Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

# Download latest release
curl -L -o bin/lobstertrap \
  "https://github.com/anthropics/lobster-trap/releases/latest/download/lobstertrap-${OS}-${ARCH}"

chmod +x bin/lobstertrap
./bin/lobstertrap --version
```

**Option B: Build from Source**

```bash
# Requirements: Go 1.21+
cd ~/projects
git clone https://github.com/anthropics/lobster-trap.git
cd lobster-trap

# Build
go build -o lobstertrap ./cmd/lobstertrap

# Copy to PLAYBOOK
cp lobstertrap ~/projects/playbook/bin/
```

### Policy File Location

```bash
# Create policy directory
mkdir -p ~/projects/playbook/policies

# Verify structure
ls -la ~/projects/playbook/policies/
# Expected: *.yaml playbook definitions
```

**Sample playbook policy (`policies/PB-INJ-001.yaml`):**
```yaml
playbook_id: PB-INJ-001
playbook_name: "Prompt Injection - Standard Response"
version: "1.0"
author: "PLAYBOOK System"
last_updated: "2025-01-15"

triggers:
  categories:
    - PROMPT_INJECTION
  severities:
    - HIGH
    - CRITICAL

steps:
  - step_id: 1
    step_name: "Immediate Deny"
    action: DENY
    description: "Block the request immediately"
    auto_execute: true
    timeout_seconds: 5

  - step_id: 2
    step_name: "Log Extended"
    action: LOG
    description: "Enable extended logging for source session"
    auto_execute: true
    timeout_seconds: 5

  - step_id: 3
    step_name: "Rate Limit"
    action: RATE_LIMIT
    description: "Apply rate limiting to source IP"
    auto_execute: true
    parameters:
      max_requests_per_minute: 10
      ban_duration_seconds: 300
    timeout_seconds: 5

  - step_id: 4
    step_name: "Human Review"
    action: HUMAN_REVIEW
    description: "Escalate to human reviewer"
    auto_execute: false
    parameters:
      notify: ["incident-response@company.com"]
      sla_minutes: 30
    timeout_seconds: 3600

completion_conditions:
  - "All auto_execute steps completed OR"
  - "HUMAN_REVIEW step acknowledged OR"
  - "Timeout (24 hours)"
```

### Log File Configuration

```bash
# Create log directory
mkdir -p ~/projects/playbook/logs/lobstertrap

# Set permissions
chmod 755 ~/projects/playbook/logs/lobstertrap

# Verify Lobster Trap can write logs
touch ~/projects/playbook/logs/lobstertrap/events.$(date +%Y%m%d).log
chmod 644 ~/projects/playbook/logs/lobstertrap/events.*.log
```

**Lobster Trap config file (`config/lobstertrap.yaml`):**
```yaml
# Lobster Trap DPI Configuration
log_level: info
log_format: json
log_output: /app/logs/lobstertrap/events.log

# Inspection rules
inspection:
  enabled: true
  mode: inline
  max_request_size: 1048576  # 1MB
  max_response_size: 2097152  # 2MB

# Pattern detection
patterns:
  injection_detection: true
  pii_detection: true
  credential_detection: true
  exfiltration_detection: true

# Actions
actions:
  default: LOG
  thresholds:
    low: 25
    medium: 50
    high: 75
    critical: 90
```

### Testing the Setup

```bash
cd ~/projects/playbook

# Test 1: Verify binary works
./bin/lobstertrap --version
# Expected: version output

# Test 2: Test configuration
./bin/lobstertrap test --config ./config/lobstertrap.yaml
# Expected: Configuration valid

# Test 3: Validate a policy file
./bin/lobstertrap test --policy-file ./policies/PB-INJ-001.yaml
# Expected: Policy valid

# Test 4: Write test log entry
echo '{"timestamp":"2025-01-15T14:30:00Z","session_id":"test_001","risk_score":85,"contains_injection_patterns":true,"intent_category":"jailbreak"}' >> logs/lobstertrap/events.$(date +%Y%m%d).log

# Test 5: Verify PLAYBOOK detects the event
curl -s http://localhost:8000/api/v1/incidents | python -m json.tool
# Expected: New incident detected from log entry
```

---

## 7. Gemini Pro API Setup

### Google AI Studio Configuration

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API key**
4. Select or create a Google Cloud project
5. Copy the generated API key

### API Key Generation

```bash
# Add to your .env file
# GEMINI_API_KEY=your_actual_key_here

# Verify the key works
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{
      "parts":[{"text": "Say hello in one word"}]
    }]
  }' | python -m json.tool

# Expected: Response with generated text "Hello"
```

### Rate Limit Awareness

| Tier | Requests/Minute | Requests/Day | Notes |
|---|---|---|---|
| Free | 60 | 1,500 | Sufficient for demo |
| Pay-as-you-go | 1,000 | 30,000 | For production use |

**Critical for PLAYBOOK:**
- **DEMO_MODE=true**: Gemini is NEVER called live. All responses come from `gemini_cache.json`.
- **45% failure rate during US peak hours** (9 AM - 6 PM EST) has been observed.
- Always pre-populate cache before demo day.

### Testing the Connection

```bash
cd ~/projects/playbook/backend
source venv/bin/activate

# Test with Python client
python -c "
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv('../.env')

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Classify: prompt injection attempt. Reply with one word.')
print(response.text)
"
# Expected: Single-word classification

# Test cache functionality
python -c "
import json
import os

# Check cache exists
if os.path.exists('./gemini_cache.json'):
    with open('./gemini_cache.json', 'r') as f:
        cache = json.load(f)
    print(f'Cache loaded: {len(cache)} entries')
else:
    print('WARNING: No cache file found. Create one with:')
    print('  python scripts/populate_gemini_cache.py')
"
```

**Pre-populate cache for demo:**
```bash
cd ~/projects/playbook/backend
source venv/bin/activate

# Run cache population script
python scripts/populate_gemini_cache.py

# Verify cache
ls -la gemini_cache.json
python -c "import json; c=json.load(open('gemini_cache.json')); print(f'{len(c)} cached responses')"
```

---

## 8. Verification Checklist

### 23-Point System Verification

Run through each item and check it off:

#### Infrastructure (1-5)
- [ ] **1. Python 3.11+ installed**: `python3.11 --version` returns 3.11.x
- [ ] **2. Node.js 18+ installed**: `node --version` returns v18.x.x
- [ ] **3. Virtual environment active**: `which python` shows venv path
- [ ] **4. All pip dependencies installed**: `pip list` shows all packages
- [ ] **5. npm dependencies installed**: `npm list` in frontend/ succeeds

#### Backend (6-12)
- [ ] **6. Database initialized**: `playbooks.db` file exists
- [ ] **7. Migrations applied**: `alembic current` shows head revision
- [ ] **8. Seed data loaded**: `GET /api/v1/incidents` returns data
- [ ] **9. Health endpoint responds**: `GET /api/v1/health` returns 200
- [ ] **10. OpenAPI docs accessible**: `/docs` shows Swagger UI
- [ ] **11. WebSocket connects**: `ws://localhost:8000/ws/incidents` connects
- [ ] **12. Environment variables loaded**: `python -c "from app.core.config import settings; print(settings.DATABASE_URL)"` returns expected value

#### Frontend (13-15)
- [ ] **13. Dev server starts**: `npm run dev` starts without errors
- [ ] **14. Dashboard loads**: Browser shows http://localhost:5173 without errors
- [ ] **15. WebSocket real-time updates**: Creating incident reflects on dashboard

#### Lobster Trap (16-17)
- [ ] **16. Binary executable**: `lobstertrap --version` returns version
- [ ] **17. Policy validation**: `lobstertrap test --policy-file` succeeds

#### Gemini (18-19)
- [ ] **18. API key valid**: Direct API call returns 200
- [ ] **19. Cache file present**: `gemini_cache.json` exists with entries

#### Integration (20)
- [ ] **20. End-to-end pipeline**: Test event flows through DETECT > CLASSIFY > RESPOND > FORENSICS

#### Judge Layer (21-23)
- [ ] **21. Judge Layer responds in <50ms**: Verify latency on classification calls meets SLA
- [ ] **22. Bypass pattern detection catches all 4 known patterns**: Test against known prompt injection bypass variants
- [ ] **23. Deterministic classification works without Gemini**: Set `JUDGE_DETERMINISTIC_MODE=true` and verify classifications still succeed

### Health Check Commands

```bash
# Run all health checks at once
echo "=== PLAYBOOK Health Check Suite ==="

# 1. Backend health
echo -n "Backend Health: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health

# 2. Database connection
echo -n "Database: "
curl -s http://localhost:8000/api/v1/health | python -c "import sys,json; print(json.load(sys.stdin)['services']['database'])"

# 3. Incident count
echo -n "Incidents: "
curl -s http://localhost:8000/api/v1/incidents | python -c "import sys,json; print(len(json.load(sys.stdin)['data']))"

# 4. Frontend reachable
echo -n "Frontend: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# 5. WebSocket
echo -n "WebSocket: "
python -c "
import asyncio, websockets
async def test():
    try:
        async with websockets.connect('ws://localhost:8000/ws/incidents', timeout=5):
            print('connected')
    except Exception as e:
        print(f'error: {e}')
asyncio.run(test())
"
```

### Log Inspection

```bash
# Backend logs (if running directly)
tail -f ~/projects/playbook/backend/logs/playbook.log

# Lobster Trap logs
tail -f ~/projects/playbook/logs/lobstertrap/events.*.log

# Docker logs
docker-compose logs -f backend

# Railway logs
railway logs --tail
```

### Common Issues Quick Fix

| Symptom | Quick Fix |
|---|---|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Database locked | `rm playbooks.db && alembic upgrade head` |
| Cache miss | `python scripts/populate_gemini_cache.py` |
| CORS error | Check `CORS_ORIGINS` includes frontend URL |
| Module not found | `pip install -r requirements.txt` |

---

## 9. Troubleshooting

### 15 Common Problems with Solutions

#### Problem 1: `ModuleNotFoundError: No module named 'fastapi'`

**Symptom:** Starting backend fails with module import error.

**Cause:** Virtual environment not activated or dependencies not installed.

**Solution:**
```bash
cd ~/projects/playbook/backend
source venv/bin/activate
pip install -r requirements.txt
```

#### Problem 2: `sqlite3.OperationalError: database is locked`

**Symptom:** API returns 500 with database lock error.

**Cause:** Multiple processes accessing SQLite simultaneously.

**Solution:**
```bash
# Kill all processes holding the database
lsof playbooks.db | awk 'NR>1 {print $2}' | xargs kill -9 2>/dev/null

# Or reset database
rm playbooks.db
alembic upgrade head
python scripts/seed_demo_data.py
```

#### Problem 3: Uvicorn `Address already in use`

**Symptom:** `ERROR: [Errno 48] Address already in use`

**Solution:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Problem 4: Frontend `ERR_CONNECTION_REFUSED`

**Symptom:** Browser cannot connect to frontend.

**Solution:**
```bash
# Check if dev server is running
curl http://localhost:5173
# If failed, restart:
cd ~/projects/playbook/frontend
npm run dev
```

#### Problem 5: CORS errors in browser console

**Symptom:** `Access to fetch blocked by CORS policy`

**Solution:**
```bash
# Ensure CORS_ORIGINS includes your frontend URL
# In .env:
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Restart backend after changing .env
```

#### Problem 6: Lobster Trap `command not found`

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'lobstertrap'`

**Solution:**
```bash
# Verify binary exists and is in PATH
ls -la ~/projects/playbook/bin/lobstertrap
export PATH="$HOME/projects/playbook/bin:$PATH"
lobstertrap --version
```

#### Problem 7: Gemini API `429 Too Many Requests`

**Symptom:** Classification fails with rate limit error.

**Solution:**
```bash
# Switch to DEMO_MODE (uses cache only)
# In .env:
DEMO_MODE=true
GEMINI_CACHE_ENABLED=true

# Or wait and retry (exponential backoff)
```

#### Problem 8: WebSocket connection fails

**Symptom:** Dashboard not receiving real-time updates.

**Solution:**
```bash
# Test WebSocket manually
python -c "
import asyncio, websockets
async def test():
    uri = 'ws://localhost:8000/ws/incidents'
    async with websockets.connect(uri) as ws:
        print('Connected!')
        await ws.send('{\"type\": \"ping\"}')
        resp = await ws.recv()
        print(f'Received: {resp}')
asyncio.run(test())
"
```

#### Problem 9: Railway deployment fails

**Symptom:** `railway up` fails or health check never passes.

**Solution:**
```bash
# Check logs
railway logs

# Verify environment variables
railway variables

# Ensure PORT uses Railway's injected variable
echo $PORT  # Should be set by Railway

# Check Procfile exists and is correct
cat backend/Procfile
```

#### Problem 10: Railway service sleeps during demo

**Symptom:** App becomes unresponsive after ~30 minutes of inactivity.

**Solution:**
- Set up UptimeRobot (Section 4.8)
- Or keep a ping running:
```bash
while true; do curl -s https://your-app.up.railway.app/api/v1/health > /dev/null; sleep 240; done
```

#### Problem 11: Seed data not appearing

**Symptom:** Dashboard shows no incidents.

**Solution:**
```bash
cd ~/projects/playbook/backend
source venv/bin/activate

# Re-run seed
python scripts/seed_demo_data.py

# Or seed manually via API
curl -X POST http://localhost:8000/api/v1/demo/seed \
  -H "Content-Type: application/json" \
  -d '{"scenario": "all"}'
```

#### Problem 12: Policy YAML syntax error

**Symptom:** `yaml.scanner.ScannerError` or playbook fails to load.

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('./policies/PB-INJ-001.yaml')); print('Valid YAML')"

# Or use yamllint
pip install yamllint
yamllint policies/
```

#### Problem 13: Docker container exits immediately

**Symptom:** `docker-compose up` starts then containers exit.

**Solution:**
```bash
# Check logs for error
docker-compose logs backend

# Common fix: rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Problem 14: Frontend build fails

**Symptom:** `npm run build` produces errors.

**Solution:**
```bash
cd ~/projects/playbook/frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Problem 15: Evidence packages not generating

**Symptom:** Forensics section shows no evidence.

**Solution:**
```bash
# Check evidence directory exists and is writable
ls -la ~/projects/playbook/evidence/
mkdir -p ~/projects/playbook/evidence
chmod 755 ~/projects/playbook/evidence

# Verify forensics engine is enabled
python -c "from app.core.config import settings; print(settings.FORENSICS_ENABLED)"
```

### Debug Mode Activation

**Enable debug logging:**
```bash
# In .env or environment
DEBUG=true
LOG_LEVEL=DEBUG
```

**Enable FastAPI debug:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

**Enable SQL query logging:**
```bash
# Add to .env
SQLALCHEMY_ECHO=true
```

### Log Locations

| Component | Log Location | Description |
|---|---|---|
| Backend | `./backend/logs/playbook.log` | Application logs |
| Uvicorn | Console output (stdout) | Server access logs |
| Lobster Trap | `./logs/lobstertrap/events.*.log` | DPI event logs |
| Frontend | Browser DevTools Console | React/Vite logs |
| Railway | `railway logs` | Cloud deployment logs |
| Docker | `docker-compose logs` | Container logs |

### Emergency Rollback

```bash
# Local development
cd ~/projects/playbook
git log --oneline -5  # Find last known good commit
git checkout <commit-hash>  # Rollback to stable commit
# Restart servers

# Railway deployment
cd ~/projects/playbook
git revert HEAD  # Revert last commit
git push origin main
railway up  # Redeploy previous version

# Docker deployment
docker-compose down
docker-compose pull  # Pull previous image tag
docker-compose up -d

# Database rollback (if migration broke)
cd ~/projects/playbook/backend
alembic downgrade -1  # Rollback one migration
# Or reset completely:
rm playbooks.db && alembic upgrade head
```

---

## 10. Demo Day Preparation

> **Note:** The Nate B Jones "AI Agent Judge Layer" article was published today -- review it before demo day for the latest architecture context on deterministic classification vs. LLM-judge approaches and SupraWall integration patterns.

### Pre-Flight Checklist (32 Items)

#### 24 Hours Before (1-10)
- [ ] **1. Git status clean**: `git status` shows no uncommitted changes
- [ ] **2. Latest code deployed**: `git log --oneline -1` shows expected commit
- [ ] **3. Railway deployment successful**: `railway status` shows `SUCCESS`
- [ ] **4. Health endpoint responsive**: `curl <production-url>/api/v1/health` returns 200
- [ ] **5. Frontend loads**: Browser opens dashboard without console errors
- [ ] **6. Demo data seeded**: Dashboard shows 5+ demo incidents
- [ ] **7. Gemini cache populated**: `gemini_cache.json` has 50+ entries
- [ ] **8. All policies valid**: `lobstertrap test --policy-file` passes for all
- [ ] **9. UptimeRobot active**: Monitor shows `Up` status
- [ ] **10. Environment variables correct**: Production uses `DEMO_MODE=true`

#### 2 Hours Before (11-20)
- [ ] **11. Service stays awake**: Health check passes after 35+ minutes
- [ ] **12. WebSocket real-time works**: New incidents appear on dashboard
- [ ] **13. All API endpoints respond**: Test `GET /incidents`, `GET /agents`, `GET /dashboard`
- [ ] **14. Evidence packages generate**: Click export on an incident works
- [ ] **15. Forensics timeline renders**: Timeline shows all 4 pipeline stages
- [ ] **16. Human review queue functional**: HUMAN_REVIEW tasks appear
- [ ] **17. Severity badges display**: CRITICAL/HIGH/MEDIUM/LOW colors correct
- [ ] **18. Analytics charts load**: `/analytics` page shows charts
- [ ] **19. Settings page accessible**: `/settings` shows configuration
- [ ] **20. Mobile responsive**: Dashboard usable on phone screen

#### 15 Minutes Before (21-30)
- [ ] **21. Browser cache cleared**: Hard refresh on dashboard
- [ ] **22. Incognito window tested**: Dashboard works in private browsing
- [ ] **23. Backup browser ready**: Secondary browser tested (Chrome + Firefox)
- [ ] **24. Terminal with logs open**: `railway logs --tail` running in background
- [ ] **25. Local backup running**: Local dev server running as fallback
- [ ] **26. API test commands ready**: curl commands in clipboard
- [ ] **27. Demo script rehearsed**: Walkthrough practiced at least once
- [ ] **28. Internet connection stable**: Speed test > 10 Mbps
- [ ] **29. Screen recording tested**: OBS/QuickTime working
- [ ] **30. Phone hotspot ready**: Mobile hotspot tested as backup internet
- [ ] **31. Practice SupraWall differentiation answer**: Be ready to explain how PLAYBOOK differs from SupraWall (deterministic classification, no dependency on external LLM at inference time, <50ms response SLA)
- [ ] **32. Practice LLM-judge vs deterministic explanation**: Rehearse explaining when deterministic classification is preferred over LLM-judge (speed, reliability, no API dependency) and when LLM-judge adds value (novel pattern detection)

### Backup Video Recording Guide

**Option A: QuickTime Player (macOS)**
```bash
# Open QuickTime
open -a QuickTime Player
# File > New Screen Recording
# Select screen area
# Click Record
# After demo: File > Save (choose location)
```

**Option B: OBS Studio (All Platforms)**
```bash
# Install: https://obsproject.com/download
# Setup:
# 1. Add Source > Display Capture
# 2. Set Output > Recording Path
# 3. Set Format: MP4
# 4. Click Start Recording
```

**Option C: Command Line (ffmpeg)**
```bash
# macOS
ffmpeg -f avfoundation -i "1:0" -r 30 demo-recording.mp4

# Linux
ffmpeg -f x11grab -r 30 -s 1920x1080 -i :0.0 demo-recording.mp4
```

**Recommended: Record a dry-run 24 hours before demo day.**

### Demo Mode Activation

```bash
# DEMO_MODE is the master switch for presentations
# When enabled:
#   - Live Gemini API calls are DISABLED
#   - All responses come from gemini_cache.json
#   - Pre-built incidents load on startup
#   - Simulation endpoints are available

# Activate via environment variable
export DEMO_MODE=true

# Or set in .env
sed -i 's/DEMO_MODE=.*/DEMO_MODE=true/' .env

# Verify activated
curl -s http://localhost:8000/api/v1/health | python -c "
import sys, json
resp = json.load(sys.stdin)
print(f'DEMO_MODE: {resp.get(\"demo_mode\", \"unknown\")}')
"

# Trigger a demo scenario
curl -X POST http://localhost:8000/api/v1/demo/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "prompt_injection",
    "severity": "high",
    "delay_seconds": 2
  }'

# Available demo scenarios:
# - data_destruction     (PocketOS scenario)
# - financial_fraud      (Step Finance scenario)
# - permission_escalation (Meta scenario)
# - harmful_output       (UnitedHealth scenario)
# - data_exfiltration    (Replit scenario)
# - prompt_injection     (Generic injection)
```

### Recovery Procedures

#### Scenario A: Production App Goes Down During Demo

```bash
# 1. Verify it's down
curl -s -o /dev/null -w "%{http_code}" https://your-app.up.railway.app/api/v1/health
# Expected: 000 or 503

# 2. Check Railway status
railway status
railway logs --tail

# 3. Quick redeploy
railway up

# 4. If deploy fails, use local as backup
cd ~/projects/playbook/backend
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# 5. Use ngrok to expose local server
ngrok http 8000
# Share the ngrok URL with judges
```

#### Scenario B: Database Corrupted

```bash
# 1. Reset database
cd ~/projects/playbook/backend
rm -f playbooks.db
alembic upgrade head
python scripts/seed_demo_data.py

# 2. Or use in-memory fallback
export DATABASE_URL=sqlite:///:memory:
# Then re-seed
```

#### Scenario C: Gemini Cache Miss

```bash
# 1. Verify cache exists
ls -la gemini_cache.json

# 2. If missing, populate quickly
cd ~/projects/playbook/backend
python -c "
import json

# Create minimal cache
cache = {
    'prompt_injection': {
        'classification': 'PROMPT_INJECTION',
        'severity': 'HIGH',
        'confidence': 0.94
    },
    'data_exfiltration': {
        'classification': 'DATA_EXFILTRATION',
        'severity': 'CRITICAL',
        'confidence': 0.98
    }
}

with open('gemini_cache.json', 'w') as f:
    json.dump(cache, f)
print('Emergency cache created')
"
```

#### Scenario D: Frontend Fails to Load

```bash
# 1. Check frontend is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# 2. Rebuild if needed
cd ~/projects/playbook/frontend
rm -rf node_modules
npm install
npm run dev

# 3. Fallback: Use curl to demonstrate API
curl -s http://localhost:8000/api/v1/incidents | python -m json.tool
```

#### Scenario E: Complete System Failure

```bash
# Nuclear option: Everything from scratch in < 5 minutes

cd ~
rm -rf playbook
git clone https://github.com/your-org/playbook.git
cd playbook/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env quickly with DEMO_MODE=true
alembic upgrade head
python scripts/seed_demo_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
cd ../frontend
npm install
npm run dev &
# Use ngrok if needed
ngrok http 8000
```

### Emergency Contacts & Resources

| Resource | URL / Command | Purpose |
|---|---|---|
| Railway Dashboard | https://railway.app/dashboard | Deployment management |
| Railway Status | https://railway.statuspage.io | Platform status |
| Google AI Studio | https://aistudio.google.com | API key management |
| Local Health | `curl localhost:8000/api/v1/health` | Backend health check |
| Deployed Health | `curl <your-url>/api/v1/health` | Production health check |
| Logs (Local) | `tail -f backend/logs/playbook.log` | Local log streaming |
| Logs (Railway) | `railway logs --tail` | Cloud log streaming |

---

## Appendix A: Quick Reference Card

### One-Line Commands

```bash
# Start everything locally (run each in separate terminals)
cd ~/projects/playbook/backend && source venv/bin/activate && uvicorn app.main:app --reload
cd ~/projects/playbook/frontend && npm run dev

# Health check
curl -s http://localhost:8000/api/v1/health | python -m json.tool

# Deploy to Railway
cd ~/projects/playbook && railway up

# Docker quick start
cd ~/projects/playbook && docker-compose up -d

# Reset everything
rm -rf ~/projects/playbook/backend/playbooks.db
# Then re-run: alembic upgrade head && python scripts/seed_demo_data.py

# View all logs
cd ~/projects/playbook/backend && source venv/bin/activate && tail -f logs/*.log
```

### Port Reference

| Service | Local Port | Purpose |
|---|---|---|
| FastAPI Backend | 8000 | REST API + WebSocket |
| React Frontend | 5173 | Development server (Vite) |
| React Frontend (alt) | 3000 | Alternative dev server |
| Railway Deployed | 443 | HTTPS production |
| Lobster Trap (local) | N/A | File I/O only |

### File Paths Quick Reference

```
~/projects/playbook/
├── .env                          # Environment variables (NEVER commit)
├── .env.template                 # Template for .env
├── backend/
│   ├── venv/                     # Python virtual environment
│   ├── playbooks.db              # SQLite database
│   ├── requirements.txt          # Python dependencies
│   ├── alembic/                  # Database migrations
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── database.py           # Database setup
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── core/
│   │   │   └── config.py         # Settings from .env
│   │   └── routers/              # API endpoints
│   ├── scripts/
│   │   ├── seed_demo_data.py     # Seed data script
│   │   └── populate_gemini_cache.py  # Cache population
│   └── logs/                     # Application logs
├── frontend/
│   ├── node_modules/             # npm packages
│   ├── src/                      # React source code
│   ├── dist/                     # Production build
│   └── package.json              # npm dependencies
├── policies/                     # YAML playbook definitions
├── logs/
│   └── lobstertrap/              # Lobster Trap log files
├── evidence/                     # Generated evidence packages
├── bin/
│   └── lobstertrap               # Lobste
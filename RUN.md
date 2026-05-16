# PLAYBOOK — Run Application Guide

## Prerequisites

- **Node.js** 18+ with npm
- **Python** 3.12+
- **Docker Desktop** with WSL2 backend
- **Git Bash** or WSL (for shell commands)

## Step 1: Start PostgreSQL (Docker in WSL)

PLAYBOOK uses PostgreSQL for production-like data storage.

```bash
# Start PostgreSQL 16 container
wsl docker run -d --name playbook-postgres \
  -e POSTGRES_USER=playbook \
  -e POSTGRES_PASSWORD=playbook123 \
  -e POSTGRES_DB=playbook \
  -p 5432:5432 postgres:16-alpine

# Verify it's running
wsl docker ps | grep playbook-postgres
```

**Connection details:**
- Host: WSL IP (get with `wsl hostname -I`)
- Port: `5432`
- Database: `playbook`
- User: `playbook`
- Password: `playbook123`

## Step 2: Backend Setup

### 2a. Create Python Virtual Environment

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
```

### 2b. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2c. Configure Environment

Create `backend/.env`:

```ini
DEMO_MODE=false
SEED_ON_STARTUP=false
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO

# GCP / Gemini (optional)
GCP_PROJECT_ID=project-1fd13dba-5264-4c78-a5c
GCP_LOCATION=global
GEMINI_MODEL_FLASH=gemini-3.1-flash-lite
GEMINI_MODEL_PRO=gemini-3.1-pro-preview

# Database — use WSL IP, not localhost
# Get WSL IP: wsl hostname -I
DATABASE_URL=postgresql+asyncpg://playbook:playbook123@<WSL_IP>:5432/playbook

# API
API_HOST=0.0.0.0
API_PORT=8001
```

**Important:** Replace `<WSL_IP>` with your actual WSL IP address:
```bash
wsl hostname -I
# Example output: 172.27.144.112
```

### 2d. Create Database Tables

```bash
python -c "
import asyncio
from app.database import engine
from app.models import Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created')

asyncio.run(create_tables())
"
```

### 2e. Seed Reference Data

This loads NIST baselines, industry templates, playbooks, detection rules, and compliance mappings:

```bash
python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.seed.all import seed_all

async def seed():
    async with AsyncSessionLocal() as db:
        results = await seed_all(db)
        for table, count in results.items():
            print(f'  + {count} {table}')
    print('Done')

asyncio.run(seed())
"
```

**Expected output:**
```
  + 4 bypass_patterns
  + 17 detection_rules
  + 17 playbooks
  + 17 nist_baselines
  + 31 compliance_mappings
  + 6 industry_templates
Done
```

### 2f. Create Demo User

```bash
python -c "
import asyncio
import bcrypt
from app.database import AsyncSessionLocal
from app.models import User, UserRole

async def create_user():
    async with AsyncSessionLocal() as db:
        password = b'demo123'
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode()
        user = User(
            email='demo@playbook.local',
            full_name='Demo User',
            hashed_password=hashed,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f'Demo user created: {user.id}')

asyncio.run(create_user())
"
```

### 2g. Start Backend Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: `http://localhost:8001`

API docs: `http://localhost:8001/docs`

## Step 3: Frontend Setup

### 3a. Install Dependencies

```bash
cd ../frontend
npm install
```

### 3b. Configure Environment

Create `frontend/.env`:

```ini
VITE_API_URL=http://localhost:8001/api/v1
VITE_WS_URL=ws://localhost:8001/api/v1/ws/incidents
```

### 3c. Start Frontend Dev Server

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend will be available at: `http://localhost:5173`

## Step 4: Login

Open `http://localhost:5173/login` and sign in with:

- **Email:** `demo@playbook.local`
- **Password:** `demo123`

## Architecture Summary

```
┌─────────────────┐     HTTP/WebSocket     ┌─────────────────┐
│   React UI      │ ◄────────────────────► │  FastAPI        │
│   (Port 5173)   │                        │  (Port 8001)    │
└─────────────────┘                        └────────┬────────┘
                                                    │
                                                    │ asyncpg
                                                    │
                                            ┌───────▼────────┐
                                            │  PostgreSQL 16 │
                                            │  (WSL Docker)  │
                                            │  (Port 5432)   │
                                            └────────────────┘
```

## Troubleshooting

### Port 8001 already in use

```bash
# Find and kill the process
powershell -Command "Get-NetTCPConnection -LocalPort 8001 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }"
```

### Docker PostgreSQL not starting

```bash
# Remove old container and restart
wsl docker rm -f playbook-postgres
wsl docker run -d --name playbook-postgres -e POSTGRES_USER=playbook -e POSTGRES_PASSWORD=playbook123 -e POSTGRES_DB=playbook -p 5432:5432 postgres:16-alpine
```

### "Can't subtract offset-naive and offset-aware datetimes"

This means some code is using `datetime.now(timezone.utc)` directly instead of the `utc_now()` helper. Check `backend/app/models.py`:

```python
def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

Always use `utc_now()` for database timestamps.

### Frontend can't connect to backend

1. Verify backend is running: `curl http://localhost:8001/api/v1/health`
2. Check CORS config in `backend/app/core/config.py` includes `http://localhost:5173`
3. Verify `VITE_API_URL` in `frontend/.env` points to `http://localhost:8001/api/v1`

## Database Migration (Alembic)

If you change models, run migrations:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Note:** Alembic migrations are currently SQLite-optimized. For PostgreSQL, use `Base.metadata.create_all()` for initial table creation.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 (via Docker/WSL) |
| Auth | JWT (PyJWT) + bcrypt |
| ORM | SQLAlchemy 2.0 with asyncpg |

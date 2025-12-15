# AI Insights Service

**AI-powered data insights and anomaly detection microservice**

---

## 🎯 Overview

This is a FastAPI-based microservice that generates AI-powered insights from time-series data, text, and other input types. It combines rule-based feature extraction with Large Language Model (LLM) natural language generation to produce actionable business insights.

---

### Component Structure
```
pythia-ai-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Environment configuration
│   ├── celery_app.py          # Celery task queue
│   ├── api/
│   │   ├── routes/            # API endpoints
│   │   │   ├── insights.py
│   │   │   ├── async_insights.py
│   │   │   ├── mock_llm.py
│   │   │   └── monitoring.py
│   │   └── dependencies.py    # Dependency injection
│   ├── models/
│   │   ├── schemas.py         # Pydantic models
│   │   └── database.py        # SQLAlchemy ORM
│   ├── database/
│   │   └── connection.py      # DB session management
│   ├── services/
│   │   ├── insight_service.py
│   │   ├── feature_extractor.py
│   │   ├── prompt_builder.py
│   │   ├── anomaly_detector.py
│   │   └── drift_monitor.py
│   ├── clients/
│   │   ├── llm_base.py        # Abstract interface
│   │   ├── gemini_client.py
│   │   ├── openai_client.py
│   │   └── mock_llm.py
│   ├── repositories/
│   │   └── insight_repository.py
│   ├── tasks/
│   │   └── insight_tasks.py   # Celery tasks
│   └── utils/
│       └── rate_limiter.py
├── tests/
│   ├── test_insights.py
│   ├── test_feature_extraction.py
│   └── test_anomaly_detection.py
├── alembic/                   # Database migrations
├── scripts/
│   ├── init_db.py
│   └── query_examples.py
├── docker-compose.yml
├── Dockerfile
├── celery_worker.py
└── requirements.txt
```

## 🏗️ Architecture

### High-Level Flow
```
Client Request(Frontend OR Backend)
    ↓
FastAPI Gateway (Validation, Rate Limiting)
    ↓
Insight Service (Orchestration)
    ├─→ Feature Extractor (Rule-based analysis)
    ├─→ Anomaly Detector (Statistical analysis)
    ├─→ Prompt Builder (Template formatting)
    └─→ LLM Client (with retry logic)
        ├─→ Gemini API
        ├─→ OpenAI API
        └─→ Mock LLM (dev/test)
    ↓
Response Builder (Merge features + LLM output)
    ↓
Database Repository (Store result)
    ↓
JSON Response
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Gemini API key (or OpenAI API key)

### Installation

**1. Clone and setup:**
```bash
git clone <repo-url>
cd pythia-ai-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
Create .env file at root level
```

**Minimum required `.env`:**
```bash
DATABASE_URL=postgresql://pythia_user:pythia_pass@localhost:5432/pythia_db
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=gemini
GEMINI_API_KEY=xxxxxxxx
```

**3. Start with Docker:**
```In your terminal
# Use the below command to start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head

# Verify the status of all the services
docker-compose ps
```

**4. Verify installation:**
```In your terminal
curl http://localhost:8000/health

# Generate test insight
curl -X POST http://localhost:8000/api/v1/generate-insight \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo",
    "tenant_id": "demo",
    "input_type": "metrics",
    "data": {
      "metric_name": "sales",
      "values": [100, 110, 120, 200]
    }
  }'
```

---

## 📖 API Docs

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs

### Core Endpoints

#### POST /api/v1/generate-insight

Generate AI-powered insights.

**Request:**
```json
{
  "user_id": "user_123",
  "tenant_id": "tenant_acme",
  "input_type": "metrics",
  "data": {
    "metric_name": "daily_revenue",
    "values": [10000, 10500, 10200, 15000]
  }
}
```

**Response:**
```json
{
  "insight_id": "uuid",
  "features": {
    "previous_value": 10200,
    "current_value": 15000,
    "change_percent": 47.06,
    "severity": "high"
  },
  "insight": {
    "summary": "Revenue experienced a significant 47% surge...",
    "severity": "high",
    "confidence": 0.89,
    "recommended_actions": ["Action 1", "Action 2"],
    "key_findings": ["Finding 1", "Finding 2"]
  },
  "metadata": {
    "processing_time_ms": 2531,
    "llm_provider": "gemini",
    "fallback_used": false
  }
}
```

#### POST /api/v1/async/generate-insight

Generate insights asynchronously (returns immediately).

**Response:**
```json
{
  "task_id": "xyz",
  "status": "submitted",
  "message": "Check status at {BASE_URL}/async/task-status/{task_id}"
}
```

#### GET /api/v1/async/task-status/{task_id}

Check async task status.

**Response:**
```json
{
  "task_id": "abc",
  "status": "SUCCESS",
  "result": {full insight}
}
```

#### GET /api/v1/insight-history/{user_id}

Retrieve historical insights.

**Query Parameters:**
- `tenant_id` (required)
- `limit` (optional, default=50)
- `severity` (optional)

---

## ⚙️ Configuration

### Environment Variables
```Create a .env file on root level
# Database
DATABASE_URL=postgresql://pythia_user:pythia_pass@localhost:5432/pythia_db

# Redis (Celery + Rate Limiting)
REDIS_URL=redis://localhost:6379/0

# LLM Provider: 'mock', 'gemini', 'openai'
LLM_PROVIDER=gemini
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30

# Gemini API
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash-lite

# OpenAI API
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.1 or any of the latest models

# Feature Extraction Thresholds (% change)
SEVERITY_THRESHOLD_CRITICAL=50
SEVERITY_THRESHOLD_HIGH=25
SEVERITY_THRESHOLD_MEDIUM=10

# Rate Limiting (per tenant)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=3600

# Server
PORT=8000
LOG_LEVEL=INFO
```
---

## 🤖 LLMs

Change `LLM_PROVIDER` in `.env`:
```In your terminal
# if Gemini
LLM_PROVIDER=gemini

# if OpenAI
LLM_PROVIDER=openai

# if Mock
LLM_PROVIDER=mock
```

Restart the service:
```In your terminal
docker-compose restart api
```
---

## 💻 Development

### If you want to run the service locally and not on dockeer, then connect to redis and postgres first and use uvicorn
```In your terminal
# Start PostgreSQL and Redis
docker-compos up db redis -d

# Run API
uvicorn app.main:app --reload --port 8000

# Run Celery worker (separate terminal)
celery -A celery_worker worker --loglevel=info
```

### Project Structure Guidelines

- **Services**: Business logic, orchestration
- **Clients**: External API integrations (LLMs)
- **Routes**: API endpoints, validation only
- **Repositories**: Database operations
- **Tasks**: Celery background jobs

---

### Manual API Testing
```In your terminal
# Test with cURL
curl -X POST http://localhost:8000/api/v1/generate-insight \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_request.json

# Load test
ab -n 100 -c 10 -T "application/json" -p payload.json \
  http://localhost:8000/api/v1/generate-insight
```

---

## 🗄️ PostgreSQL

### Connecting to Database
```In your terminal
# Via Docker
docker-compose exec db psql -U pythia_user -d pythia_db

# Locally
psql -U pythia_user -d pythia_db -h localhost
```


### Database Migrations
```In your terminal
# Create new migration
docker-compose exec api alembic revision -m "description"

# Run migrations
docker-compose exec api alembic upgrade head

# Rollback one version
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

---

## 🔄 Celery & Redis

### Starting Services
```In your terminal
# Start all
docker-compose up -d

# Just Celery worker
docker-compose up celery-worker -d

# View worker logs
docker-compose logs -f celery-worker
```

### Submitting Async Tasks
```In your terminal
curl -X POST http://localhost:8000/api/v1/async/generate-insight \
  -H "Content-Type: application/json" \
  -d '{...}'

# Response: {"task_id": "abc-123", "status": "submitted"}

curl http://localhost:8000/api/v1/async/task-status/abc-123
```

### Redis Commands
```In your terminal
# Connect to Redis
docker-compose exec redis redis-cli

# Check connection
PING  # Response: PONG

# View all keys
KEYS *

# Get queue length
LLEN celery

# Flush all data (careful!)
FLUSHDB
```

---

### Environment-Specific Configs

**Development:**
```bash
LLM_PROVIDER=mock
LOG_LEVEL=DEBUG
RATE_LIMIT_REQUESTS=1000
```

**Staging:**
```bash
LLM_PROVIDER=gemini
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=5000
```

**Production:**
```bash
LLM_PROVIDER=openai
LOG_LEVEL=WARNING
RATE_LIMIT_REQUESTS=10000
WORKERS=16
```

### Health Checks
```bash
# Service health
curl http://localhost:8000/health

# Database check
docker-compose exec db pg_isready -U pythia_user

# Redis check
docker-compose exec redis redis-cli ping
```

---

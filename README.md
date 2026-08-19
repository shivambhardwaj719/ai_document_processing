# Production-Ready AI Document Processing Backend

An enterprise-grade Django REST Framework application for asynchronous document upload, text extraction (PDF, DOCX, TXT), enriched document intelligence, streaming LLM analysis, prompt template management, request logging middleware, and containerized deployment built with Python 3.11+, PostgreSQL/SQLite, Celery, Redis, Docker, and OpenAPI documentation.

---

## 1. Project Overview

This backend system provides a production-level API for uploading documents, validating content securely, extracting raw text using format-specific extractors, and processing text asynchronously using OpenAI-compatible Large Language Models (LLMs) to produce rich, validated structured JSON analysis (`title`, `summary`, `document_category`, `confidence_score`, `entities`, `section_breakdown`, `keywords`, etc.).

### Implemented Enhancements & Bonus Features:
1. 🐳 **Docker Support (Bonus Feature)**: Fully containerized application with `Dockerfile` and `docker-compose.yml` orchestrating `web`, `celery_worker`, and `redis` services.
2. ⚡ **Celery Background Processing (Bonus Feature)**: Document extraction and LLM requests are processed asynchronously using Celery and Redis. Supports synchronous fallback & eager mode (`CELERY_TASK_ALWAYS_EAGER`) for development.
3. 🧪 **Comprehensive Unit Test Suite (Bonus Feature)**: 21 unit & integration tests written with `pytest-django` covering models, format extractors, LLM services, REST API views, streaming, and middleware.
4. 🔄 **Retry & Timeout Logic for LLM Calls (Bonus Feature)**: Exponential backoff retries and configurable timeout mechanisms to handle transient API failures gracefully.
5. 🌊 **Streaming LLM Responses (Bonus Feature)**: Real-time Server-Sent Events (SSE) streaming via `GET /api/v1/documents/{id}/stream/`.
6. 📝 **Configurable Prompt Templates (Bonus Feature)**: Dynamic prompt registry (`apps/documents/prompts/templates.py`) supporting templates (`default`, `resume`, `contract`, `general`) and environment override (`LLM_PROMPT_OVERRIDE`).
7. 📊 **HTTP Request Logging Middleware (Bonus Feature)**: Structured JSON middleware (`RequestLoggingMiddleware`) capturing HTTP method, path, remote IP, status code, latency (ms), and query parameters.

---

## 2. Technology Stack

- **Backend**: Python 3.11+, Django 5.0, Django REST Framework
- **Database**: PostgreSQL / SQLite (for local development)
- **Background Worker & Broker**: Celery, Redis
- **Containerization**: Docker, Docker Compose
- **Testing & Code Quality**: Pytest, Pytest-Django, Ruff
- **Document Processors**: PyPDF, python-docx
- **AI & Schemas**: OpenAI-compatible HTTP Integration, Pydantic 2.5+
- **API Documentation**: Swagger UI (`/swagger/` & `/`) & Postman Collection

---

## 3. Architecture

```text
                               ┌─────────────────┐
                               │   REST Client   │
                               └────────┬────────┘
                                        │
                                        ▼
                            ┌──────────────────────┐
                            │ Django REST API      │
                            │ (POST /v1/documents/)│
                            └───────────┬──────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌──────────────────────┐                ┌──────────────────────┐
        │ Database (Postgres)  │                │    Redis Broker      │
        └──────────────────────┘                └───────────┬──────────┘
                                                            │
                                                            ▼
                                                ┌──────────────────────┐
                                                │    Celery Worker     │
                                                └───────────┬──────────┘
                                                            │
                                    ┌───────────────────────┴───────────────────────┐
                                    ▼                                               ▼
                        ┌──────────────────────┐                        ┌──────────────────────┐
                        │ Document Extractors  │                        │ OpenAI / LLM API     │
                        │ (PDF / DOCX / TXT)   │                        │ (Retry & Timeout)    │
                        └──────────────────────┘                        └──────────────────────┘
```

---

## 4. Project Structure

```text
ai_document_processing/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── pytest.ini
├── manage.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── celery.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── common/
│   │   ├── health_views.py     # System Health Check (/health/)
│   │   ├── messages.py
│   │   └── response_handler.py
│   │
│   └── documents/
│       ├── models.py           # Document model & status choices
│       ├── tasks.py            # Celery background tasks
│       ├── middleware.py       # Request logging & custom exception handler
│       ├── urls.py             # App URL routing
│       │
│       ├── api/
│       │   └── v1/
│       │       ├── document_views.py       # Upload, List, Detail & SSE Streaming APIViews
│       │       ├── document_serializers.py # DRF serializers
│       │       └── urls.py                 # Versioned API routes
│       │
│       ├── prompts/           # Configurable prompt templates registry
│       │   └── templates.py
│       │
│       ├── extractors/         # Format-specific extractors & factory
│       │   ├── base.py
│       │   ├── pdf.py
│       │   ├── docx.py
│       │   ├── txt.py
│       │   └── factory.py
│       │
│       ├── services/          # Service layer logic
│       │   ├── document_service.py
│       │   ├── extraction_service.py
│       │   ├── llm_service.py  # LLM API integration with Retries, Timeout & Streaming
│       │   └── processing_service.py
│       │
│       ├── tests/             # Comprehensive Pytest test suite
│       │   ├── conftest.py
│       │   ├── test_api.py
│       │   ├── test_extractors.py
│       │   ├── test_middleware.py
│       │   ├── test_models.py
│       │   └── test_services.py
│       │
│       ├── schemas/           # Pydantic schemas
│       │   └── llm_response.py
│       │
│       └── utils/             # Validation & logging utilities
│           ├── file_validation.py
│           └── logging.py
│
└── static/
    └── docs/
        ├── swagger.yml
        └── postman_collection.json
```

---

## 5. Quick Start with Docker 🐳

The easiest way to run the entire stack (Django API, Celery Worker, Redis) is using Docker Compose.

```bash
# 1. Clone the repository and enter directory
cd ai_document_processing

# 2. Build and start containers
docker compose up --build
```

The application will be accessible at `http://localhost:8000`.

---

## 6. Setup & Running Locally (Without Docker)

### Step 1: Environment Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env
```

### Step 2: Database Migrations

```bash
python manage.py migrate
```

### Step 3: Run Celery Worker (Optional in local dev)

```bash
# Ensure Redis server is running
celery -A config worker --loglevel=info
```

*Note: In local development, `CELERY_TASK_ALWAYS_EAGER=True` is enabled by default so document tasks execute synchronously without requiring an active Celery worker.*

### Step 4: Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access endpoints:
- **API Swagger Documentation**: `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/swagger/`
- **Health Check**: `http://127.0.0.1:8000/health/`

---

## 7. Running Tests 🧪

Run the unit test suite and linting checks:

```bash
# Run pytest test suite
pytest -v

# Run ruff code linter
ruff check .
```

---

## 8. Environment Variables

| Variable Name | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django Secret Key | `django-insecure-...` |
| `DJANGO_DEBUG` | Enable Debug Mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Allowed HTTP Host headers | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database Connection URL | `sqlite:///db.sqlite3` |
| `CELERY_BROKER_URL` | Redis URL for Celery broker | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery result backend | `redis://127.0.0.1:6379/0` |
| `CELERY_TASK_ALWAYS_EAGER` | Run Celery tasks synchronously in dev | `True` |
| `LLM_API_KEY` | OpenAI / Compatible API key (`mock-api-key` for offline testing) | `mock-api-key` |
| `LLM_BASE_URL` | LLM HTTP API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | LLM Model Name | `gpt-4o-mini` |
| `LLM_TIMEOUT` | Request timeout in seconds | `30` |
| `LLM_MAX_RETRIES` | Max retries for transient errors | `3` |
| `LLM_PROMPT_OVERRIDE` | Optional system prompt override | `""` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed file upload size (MB) | `10` |

---

## 9. API Usage Examples

### Health Check

```bash
curl -X GET http://127.0.0.1:8000/health/
```

### 1. Upload Document (`POST /api/v1/documents/`)

**Request:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/documents/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-From-Swagger: true' \
  -F 'file=@Assignment-AI.pdf;type=application/pdf'
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "id": "991f3740-2ddd-4e88-9458-23f8f34e089e",
    "filename": "Assignment-AI.pdf",
    "status": "PENDING",
    "file_type": "pdf",
    "file_size": 99560,
    "mime_type": "application/pdf",
    "content_hash": "06c3fa6e56301d0bf8fe8f38f85045200cd036c21ff79dd7bfa98ffad7f1f998",
    "created_at": "2026-08-19T12:04:11.248464Z",
    "processed_at": null,
    "error_message": null,
    "task_id": "ba36e20f-dae1-4898-bf37-1157f1793728",
    "retry_count": 0,
    "analysis": null
  },
  "message": "Document uploaded successfully and queued for background analysis."
}
```

---

### 2. List Documents (`GET /api/v1/documents/`)

**Request:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/documents/?page=1&page_size=10' \
  -H 'accept: application/json' \
  -H 'X-From-Swagger: true'
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 4,
  "next": null,
  "previous": null,
  "data": [
    {
      "id": "991f3740-2ddd-4e88-9458-23f8f34e089e",
      "filename": "Assignment-AI.pdf",
      "status": "COMPLETED",
      "file_type": "pdf",
      "file_size": 99560,
      "created_at": "2026-08-19T12:04:11.248464Z",
      "processing_completed_at": "2026-08-19T12:06:11.010573Z"
    },
    {
      "id": "a2d71b1f-54c4-4051-99a7-6fe21086d421",
      "filename": "Sivam-Bhardwaj.pdf",
      "status": "COMPLETED",
      "file_type": "pdf",
      "file_size": 300684,
      "created_at": "2026-08-18T15:40:28.708837Z",
      "processing_completed_at": "2026-08-18T15:40:31.905930Z"
    }
  ],
  "message": "Documents retrieved successfully."
}
```

---

### 3. Get Document Detail (`GET /api/v1/documents/{id}/`)

**Request:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/documents/991f3740-2ddd-4e88-9458-23f8f34e089e/' \
  -H 'accept: application/json' \
  -H 'X-From-Swagger: true'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "991f3740-2ddd-4e88-9458-23f8f34e089e",
    "filename": "Assignment-AI.pdf",
    "status": "COMPLETED",
    "file_type": "pdf",
    "file_size": 99560,
    "mime_type": "application/pdf",
    "content_hash": "06c3fa6e56301d0bf8fe8f38f85045200cd036c21ff79dd7bfa98ffad7f1f998",
    "created_at": "2026-08-19T12:04:11.248464Z",
    "processed_at": "2026-08-19T12:06:11.010573Z",
    "error_message": null,
    "task_id": "ba36e20f-dae1-4898-bf37-1157f1793728",
    "retry_count": 0,
    "analysis": {
      "title": "Document Intelligence Analysis (Python)",
      "summary": "Comprehensive analysis of the uploaded document (Technical Specification). Content overview: Python & AI Backend Engineer – Technical Assessment Objective Build a Django REST API that accepts a document, extracts its text, sends the content to an LLM, and returns a structured summary. Requirements 1. Django Project Create a Django REST...",
      "document_category": "Technical Specification",
      "confidence_score": 0.98,
      "sentiment_tone": "Professional & Objective",
      "readability_level": "Intermediate",
      "executive_takeaway": "This technical specification contains 472 words covering Python, Backend, Engineer.",
      "keywords": [
        "Python",
        "Backend",
        "Engineer",
        "Technical",
        "Assessment",
        "Objective",
        "Build",
        "Django"
      ],
      "key_insights": [
        "Document focuses primarily on Python and related concepts.",
        "Contains approximately 472 words structured across multiple key topics.",
        "Processed and validated with 98% AI extraction confidence score."
      ],
      "section_breakdown": [
        {
          "heading": "Document Overview",
          "summary": "Initial section introducing core content: Python & AI Backend Engineer – Technical Assessment Objective Build a Django RES..."
        },
        {
          "heading": "Main Content & Specifications",
          "summary": "Detailed coverage involving Python, Backend, Engineer, Technical."
        }
      ],
      "action_items": [
        "Review extracted metadata and section summaries for accuracy."
      ],
      "entities": {
        "organizations": [
          "Telepathy Infotech",
          "AI Document Processing Corp"
        ],
        "dates": [
          "August 2026"
        ],
        "locations": [
          "India",
          "Global"
        ],
        "people": [
          "Document Author"
        ],
        "monetary_amounts": [
          "$0.00 (Processed)"
        ],
        "emails_and_contacts": [
          "contact@example.com"
        ]
      },
      "metadata_metrics": {
        "reading_time_minutes": 2.4,
        "key_technologies_mentioned": [
          "Python",
          "Django",
          "Docker",
          "Celery"
        ],
        "urgency_level": "Informational"
      },
      "language": "English",
      "word_count": 472
    }
  },
  "message": "Document details retrieved successfully."
}
```

---

### 4. Stream Document Analysis (`GET /api/v1/documents/{id}/stream/`)

**Request:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/documents/991f3740-2ddd-4e88-9458-23f8f34e089e/stream/?template=resume' \
  -H 'accept: text/event-stream' \
  -H 'X-From-Swagger: true'
```

**Response (200 OK - Server-Sent Events):**
```http
data: {"chunk": "{\n", "done": false}

data: {"chunk": "  \"title\": \"Document Intelligence Analysis (Python)\",\n", "done": false}

data: {"chunk": "  \"summary\": \"Comprehensive analysis of the uploaded document (Technical Specification)...\",\n", "done": false}

data: {"chunk": "  \"document_category\": \"Technical Specification\",\n", "done": false}

...

data: {"chunk": "}", "done": false}

data: {"event": "completed", "result": {"title": "Document Intelligence Analysis (Python)", "summary": "Comprehensive analysis of the uploaded document...", "document_category": "Technical Specification", "confidence_score": 0.98, "keywords": ["Python", "Backend", "Engineer"], "entities": {"organizations": ["Telepathy Infotech", "AI Document Processing Corp"]}, "metadata_metrics": {"reading_time_minutes": 2.4, "key_technologies_mentioned": ["Python", "Django", "Docker", "Celery"]}}, "done": true}
```

---

## 10. Design Decisions & Security

1. **Security**:
   - Files are validated against magic bytes headers (`%PDF-`, `PK\x03\x04`) to prevent malicious file extension spoofing.
   - Internal storage filenames incorporate UUIDs to prevent file overwrite collisions or directory traversal attacks.
   - Central exception handling ensures internal exception stack traces and secrets are never exposed to API clients.

2. **Performance & Observability**:
   - Celery background processing prevents long HTTP request blocks during text extraction and LLM calls.
   - `RequestLoggingMiddleware` provides JSON observability across HTTP latency, IP, status code, and endpoint paths.
   - Standardized indexes on `(status, created_at)`, `(file_type, created_at)`, and `content_hash` optimize database queries.

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

### 1. Upload Document

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/ \
  -F "file=@/path/to/sample.pdf"
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "id": "e6a7153b-857c-473d-9d41-38e2ecad03a1",
    "filename": "sample.pdf",
    "status": "COMPLETED",
    "file_type": "pdf",
    "file_size": 45210,
    "mime_type": "application/pdf",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "created_at": "2026-08-19T10:00:00Z",
    "processed_at": "2026-08-19T10:00:05Z",
    "error_message": null,
    "task_id": "7b89f31a-4d2c-491a-8212-0012abcde345",
    "retry_count": 0,
    "analysis": {
      "title": "Document Intelligence Analysis",
      "summary": "Comprehensive analysis of document...",
      "document_category": "Technical Specification",
      "confidence_score": 0.98
    }
  },
  "message": "Document uploaded successfully and queued for background analysis."
}
```

### 2. List Documents (Paginated & Filtered)

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/documents/?status=COMPLETED&file_type=pdf&page=1&page_size=10"
```

### 3. Get Document Detail

```bash
curl -X GET http://127.0.0.1:8000/api/v1/documents/e6a7153b-857c-473d-9d41-38e2ecad03a1/
```

### 4. Stream Document Analysis (Server-Sent Events)

```bash
curl -N -X GET "http://127.0.0.1:8000/api/v1/documents/e6a7153b-857c-473d-9d41-38e2ecad03a1/stream/?template=resume" \
  -H "accept: text/event-stream"
```

**SSE Stream Response:**
```http
data: {"chunk": "{\n", "done": false}

data: {"chunk": "  \"title\": \"Document Intelligence Analysis\",\n", "done": false}

...

data: {
data:   "event": "completed",
data:   "result": { ... },
data:   "done": true
data: }
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

# Production-Ready AI Document Processing Backend

An enterprise-grade Django REST Framework application for asynchronous document upload, text extraction (PDF, DOCX, TXT), and structured LLM analysis built with Python 3.12+, PostgreSQL/SQLite, Celery, Redis, and OpenAPI documentation.

---

## 1. Project Overview

This backend system provides a production-level API for uploading documents, validating their content securely, extracting raw text using format-specific extractors, and processing the text asynchronously using OpenAI-compatible Large Language Models (LLMs) to produce validated structured JSON analysis (`title`, `summary`, `keywords`, `language`, `word_count`).

### Key Highlights & Implemented Bonus Enhancements:
1. **Celery Background Processing (Bonus Feature)**: Document upload immediately returns `202 Accepted` while Celery background workers handle text extraction and LLM processing asynchronously without blocking API threads.
2. **Retry Logic for LLM Calls (Bonus Feature)**: Robust exponential backoff retries and request timeouts handling transient API failures gracefully.
3. **Strict Content Validation**: File headers are inspected using magic bytes to prevent spoofing, path traversal, or corrupted payload uploads.
4. **Factory Extraction Architecture**: Decoupled extractor classes (`PDFExtractor`, `DOCXExtractor`, `TXTExtractor`) inheriting from `BaseExtractor`.
5. **Structured Schema Validation**: Pydantic schema validation enforcing output format for LLM responses.
6. **Modular API Architecture**: Versioned API layout under `apps/documents/api/v1/`.

---

## 2. Technology Stack

- **Backend**: Python 3.12+, Django 5.0, Django REST Framework
- **Database**: PostgreSQL / SQLite (for local development)
- **Background Worker & Broker**: Celery, Redis
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
│       ├── middleware.py       # Centralized exception handling
│       ├── urls.py             # App URL routing
│       │
│       ├── api/
│       │   └── v1/
│       │       ├── document_views.py       # Document Upload, List & Detail APIViews
│       │       ├── document_serializers.py # DRF serializers
│       │       └── urls.py                 # Versioned API routes
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
│       │   ├── llm_service.py  # LLM API integration with Retries & Timeout
│       │   └── processing_service.py
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

## 5. Setup & Running Locally

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

### Step 3: Run Celery Worker (In a separate terminal)

```bash
# Ensure Redis server is running
celery -A config worker --loglevel=info
```

### Step 4: Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access endpoints:
- **API Swagger Documentation**: `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/swagger/`
- **Health Check**: `http://127.0.0.1:8000/health/`

---

## 6. Environment Variables

| Variable Name | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django Secret Key | `django-insecure-...` |
| `DJANGO_DEBUG` | Enable Debug Mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Allowed HTTP Host headers | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database Connection URL | `sqlite:///db.sqlite3` |
| `CELERY_BROKER_URL` | Redis URL for Celery broker | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery result backend | `redis://127.0.0.1:6379/0` |
| `LLM_API_KEY` | OpenAI / Compatible API key (`mock-api-key` for offline testing) | `mock-api-key` |
| `LLM_BASE_URL` | LLM HTTP API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | LLM Model Name | `gpt-4o-mini` |
| `LLM_TIMEOUT` | Request timeout in seconds | `30` |
| `LLM_MAX_RETRIES` | Max retries for transient errors | `3` |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed file upload size (MB) | `10` |

---

## 7. API Usage Examples

### Health Check

```bash
curl -X GET http://127.0.0.1:8000/health/
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
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
    "status": "PENDING",
    "file_type": "pdf",
    "file_size": 45210,
    "mime_type": "application/pdf",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "created_at": "2026-08-19T10:00:00Z",
    "processed_at": null,
    "error_message": null,
    "task_id": "7b89f31a-4d2c-491a-8212-0012abcde345",
    "retry_count": 0,
    "analysis": null
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

**Response (200 OK):**
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
      "title": "Quarterly Financial Analysis",
      "summary": "The document presents a comprehensive financial review of performance with growth metrics.",
      "keywords": ["Finance", "Quarterly Report", "Revenue", "Growth"],
      "language": "English",
      "word_count": 1420
    }
  }
}
```

---

## 8. Design Decisions & Security

1. **Security**:
   - Files are validated against magic bytes headers (`%PDF-`, `PK\x03\x04`) to prevent malicious file extension spoofing.
   - Internal storage filenames incorporate UUIDs to prevent file overwrite collisions or directory traversal attacks.
   - Central exception handling ensures internal exception stack traces and secrets are never exposed to API clients.

2. **Performance & Optimization**:
   - Celery background processing prevents long HTTP request blocks during text extraction and LLM calls.
   - Standardized indexes on `(status, created_at)`, `(file_type, created_at)`, and `content_hash` optimize database queries.

import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from redis import Redis

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint returning DB and Redis status.
    GET /health/
    """
    status_data = {
        "status": "healthy",
        "services": {
            "database": "unknown",
            "redis": "unknown",
        },
    }

    try:
        connection.ensure_connection()
        status_data["services"]["database"] = "healthy"
    except Exception as exc:
        logger.error("Health check DB connection failed: %s", exc)
        status_data["services"]["database"] = "unhealthy"
        status_data["status"] = "unhealthy"

    try:
        redis_url = getattr(settings, "REDIS_URL", getattr(settings, "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"))
        redis_client = Redis.from_url(redis_url, socket_connect_timeout=2)
        redis_client.ping()
        status_data["services"]["redis"] = "healthy"

    except Exception as exc:
        logger.warning("Health check Redis connection warning: %s", exc)
        status_data["services"]["redis"] = "unhealthy"
        if status_data["status"] == "healthy":
            status_data["status"] = "degraded"

    http_status = 200 if status_data["status"] in ("healthy", "degraded") else 503
    return JsonResponse(status_data, status=http_status)

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView

from apps.common.health_views import health_check

urlpatterns = [
    path("", TemplateView.as_view(template_name="swagger.html"), name="swagger-home"),
    path("health/", health_check, name="health_check"),
    path("api/v1/documents/", include("apps.documents.urls")),
    path(
        "swagger/",
        TemplateView.as_view(
            template_name="swagger.html", extra_context={"schema_url": "openapi-schema"}
        ),
        name="swagger",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

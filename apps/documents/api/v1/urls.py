from django.urls import path

from apps.documents.api.v1.document_views import (
    DocumentDetailView,
    DocumentListUploadView,
    DocumentStreamView,
)

app_name = "documents"

urlpatterns = [
    path("", DocumentListUploadView.as_view(), name="document-list-upload"),
    path("<uuid:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:pk>/stream/", DocumentStreamView.as_view(), name="document-stream"),
]

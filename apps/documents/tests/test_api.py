import uuid

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestDocumentAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_list_documents_success(self, api_client, sample_document):
        url = reverse("documents:document-list-upload")
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["success"] is True
        assert len(response.data["data"]) >= 1

    def test_list_documents_invalid_status_filter(self, api_client):
        url = reverse("documents:document-list-upload") + "?status=INVALID_STATUS"
        response = api_client.get(url)
        assert response.status_code == 400
        assert response.data["success"] is False
        assert response.data["error"]["code"] == "INVALID_FILTER"

    def test_upload_document_success(self, api_client, dummy_txt_file):
        url = reverse("documents:document-list-upload")
        response = api_client.post(url, {"file": dummy_txt_file}, format="multipart")
        assert response.status_code == 202
        assert response.data["success"] is True
        assert "id" in response.data["data"]

    def test_get_document_detail_success(self, api_client, sample_document):
        url = reverse("documents:document-detail", kwargs={"pk": sample_document.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["data"]["id"] == str(sample_document.id)

    def test_get_document_detail_not_found(self, api_client):
        url = reverse("documents:document-detail", kwargs={"pk": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.data["success"] is False
        assert response.data["error"]["code"] == "NOT_FOUND"

    def test_stream_document_analysis_success(self, api_client, sample_document):
        url = reverse("documents:document-stream", kwargs={"pk": sample_document.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"

    def test_stream_document_analysis_with_event_stream_accept_header(self, api_client, sample_document):
        url = reverse("documents:document-stream", kwargs={"pk": sample_document.id})
        response = api_client.get(url, HTTP_ACCEPT="text/event-stream")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"


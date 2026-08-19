from rest_framework import serializers

from apps.documents.models import Document
from apps.documents.utils.file_validation import validate_uploaded_file


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True, help_text="Document file (.pdf, .docx, .txt)")

    def validate_file(self, value):
        validate_uploaded_file(value)
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source="original_filename")

    class Meta:
        model = Document
        fields = [
            "id",
            "filename",
            "status",
            "file_type",
            "file_size",
            "created_at",
            "processing_completed_at",
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source="original_filename")
    analysis = serializers.JSONField(source="llm_response", allow_null=True)
    processed_at = serializers.DateTimeField(source="processing_completed_at", allow_null=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "filename",
            "status",
            "file_type",
            "file_size",
            "mime_type",
            "content_hash",
            "created_at",
            "processed_at",
            "error_message",
            "task_id",
            "retry_count",
            "analysis",
        ]

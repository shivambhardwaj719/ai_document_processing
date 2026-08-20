import hashlib
import os
import re
import uuid

from django.conf import settings
from rest_framework.exceptions import ValidationError


def sanitize_filename(filename: str) -> str:
    """
    Sanitize client filename to prevent directory traversal and header injection.
    """
    if not filename:
        return "unnamed_file"

    filename = os.path.basename(filename)
    filename = filename.replace("\x00", "")
    filename = re.sub(r"[^\w\.\-]", "_", filename)

    return filename[:200] if len(filename) > 200 else filename


def generate_stored_filename(original_filename: str) -> str:
    """
    Generate a safe, unique server-side filename incorporating UUID.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = uuid.uuid4().hex
    safe_base = sanitize_filename(os.path.splitext(original_filename)[0])
    return f"{safe_base}_{unique_id}{ext}"


def compute_file_hash(file_obj) -> str:
    """
    Calculate SHA-256 hash of file content.
    """
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def validate_magic_bytes(file_obj, ext: str) -> bool:
    """
    Validate magic byte headers for uploaded file types.
    """
    header = file_obj.read(2048)
    file_obj.seek(0)

    if not header:
        return False

    if ext == ".pdf":
        return bool(header.startswith(b"%PDF-"))
    elif ext == ".docx":
        return bool(header.startswith(b"PK\x03\x04"))
    elif ext == ".txt":
        try:
            header.decode("utf-8")
            return True
        except UnicodeDecodeError:
            try:
                header.decode("latin-1")
                return True
            except Exception:
                return False

    return False


def validate_uploaded_file(uploaded_file):
    """
    Comprehensive strict file validation function for DRF API uploads.

    Checks:
    - Non-empty file
    - File size limits
    - Allowed extension
    - Allowed MIME type
    - Magic bytes header signature matching extension
    """
    if not uploaded_file:
        raise ValidationError({"file": "No file was uploaded."})

    filename = uploaded_file.name
    if not filename:
        raise ValidationError({"file": "Uploaded file must have a filename."})

    size = uploaded_file.size
    if size == 0:
        raise ValidationError({"file": "Empty files are not allowed."})

    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    if size > max_size:
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        raise ValidationError(
            {"file": f"File size ({size / (1024*1024):.2f}MB) exceeds limit of {max_mb}MB."}
        )

    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed_exts = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise ValidationError(
            {"file": f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_exts}."}
        )

    content_type = getattr(uploaded_file, "content_type", "").lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }
    expected_mime = mime_map.get(ext)

    if content_type and content_type not in settings.ALLOWED_MIME_TYPES:
        if content_type != "application/octet-stream":
            raise ValidationError(
                {"file": f"Invalid MIME type '{content_type}' for extension '{ext}'."}
            )

    if not validate_magic_bytes(uploaded_file, ext):
        raise ValidationError(
            {"file": f"File content does not match expected format for extension '{ext}'."}
        )

    return {
        "original_filename": sanitize_filename(filename),
        "ext": ext.lstrip("."),
        "size": size,
        "mime_type": expected_mime or content_type or "application/octet-stream",
    }

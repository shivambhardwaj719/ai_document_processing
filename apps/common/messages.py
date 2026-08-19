"""
Centralized Response Messages for the AI Document Processing Application.
"""


class ResponseMessages:
    SUCCESS = "Success"
    WARNING = "Warning"
    BAD_REQUEST = "Bad Request"
    DOCUMENT_UPLOAD_SUCCESS = "Document uploaded successfully and queued for background analysis."
    DOCUMENT_LIST_SUCCESS = "Documents retrieved successfully."
    DOCUMENT_DETAIL_SUCCESS = "Document details retrieved successfully."
    DOCUMENT_NOT_FOUND = "Document with the specified ID was not found."
    INVALID_STATUS_FILTER = (
        "Invalid status filter. Valid choices are: PENDING, PROCESSING, COMPLETED, FAILED."
    )
    INVALID_FILE_TYPE_FILTER = "Invalid file_type filter. Valid choices are: pdf, docx, txt."

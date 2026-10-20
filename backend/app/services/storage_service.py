"""
Storage and file validation service for resume uploads (Phase 21: Security Hardening).
Provides secure temporary local storage, strict PDF validation,
anti-path-traversal protection, and sanitized unique filename generation.
"""
import os
import re
import uuid
import time
import logging
from pathlib import Path
from typing import Tuple
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Dangerous PDF object tokens commonly associated with malware payloads
SUSPICIOUS_PDF_TOKENS = [
    b"/Launch",
    b"/EmbeddedFiles",
    b"/RichMedia",
]


class FileValidationError(Exception):
    """Custom exception raised when file validation fails."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class StorageService:
    """
    Handles file validation and temporary local disk storage with strict security boundaries.
    """

    def __init__(self, temp_dir: str = settings.UPLOAD_TEMP_DIR):
        self.temp_dir = Path(temp_dir).resolve()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create the temporary directory if it does not already exist."""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback to system /tmp if custom directory creation fails
            self.temp_dir = Path("/tmp/ai_resume_parser_resumes").resolve()
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate_filename_and_mime(self, filename: str | None, content_type: str | None) -> str:
        """
        Validates the uploaded file extension and MIME type.
        Removes null bytes and directory separators.
        """
        if not filename or not filename.strip():
            raise FileValidationError("File name is missing or empty.", status_code=400)

        # Sanitize original filename (strip null bytes and directory traversal components)
        sanitized = filename.replace("\0", "").strip()
        clean_name = os.path.basename(sanitized)
        if not clean_name or clean_name in (".", ".."):
            raise FileValidationError("Invalid filename specified.", status_code=400)

        ext = os.path.splitext(clean_name)[1].lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file extension '{ext}'. Only PDF documents (.pdf) are accepted.",
                status_code=400
            )

        if content_type:
            normalized_mime = content_type.lower().split(";")[0].strip()
            if normalized_mime not in settings.ALLOWED_MIME_TYPES:
                raise FileValidationError(
                    f"Unsupported MIME type '{content_type}'. Expected 'application/pdf'.",
                    status_code=400
                )

        return clean_name

    def validate_file_content(self, content: bytes) -> None:
        """
        Validates raw file content:
        - Non-empty check
        - Maximum size limit check
        - PDF magic bytes (%PDF-) check
        - Basic structural corruption check (%%EOF)
        - Malicious action inspection (/Launch, /EmbeddedFiles)
        """
        size = len(content)
        if size == 0:
            raise FileValidationError("Uploaded file is empty (0 bytes).", status_code=400)

        if size > settings.max_upload_size_bytes:
            max_mb = settings.MAX_UPLOAD_SIZE_MB
            raise FileValidationError(
                f"File size ({size / (1024 * 1024):.1f}MB) exceeds maximum allowed limit of {max_mb}MB.",
                status_code=413
            )

        # Minimum realistic PDF size
        if size < 32:
            raise FileValidationError("File is too small to be a valid PDF document.", status_code=400)

        # Check for PDF magic bytes within the first 1024 bytes (ISO 32000-1)
        header_chunk = content[:1024]
        if b"%PDF-" not in header_chunk:
            raise FileValidationError(
                "Invalid PDF signature. The file does not start with standard '%PDF-' magic bytes.",
                status_code=400
            )

        # Check for EOF marker in the tail of the document (last 2048 bytes)
        tail_chunk = content[-2048:] if size > 2048 else content
        if b"%%EOF" not in tail_chunk:
            raise FileValidationError(
                "Corrupted PDF file. The file is missing the required '%%EOF' end-of-file marker.",
                status_code=400
            )

        # Malicious PDF action inspection
        for token in SUSPICIOUS_PDF_TOKENS:
            if token in content:
                logger.warning("Suspicious PDF token '%s' detected in uploaded file", token.decode("latin1", errors="ignore"))
                raise FileValidationError(
                    f"PDF contains disallowed interactive or executable construct ({token.decode('latin1')}).",
                    status_code=400,
                )

    def generate_safe_filename(self, original_filename: str) -> str:
        """
        Generates a unique, path-safe filename to prevent overwrites,
        traversal attacks, or collision.
        """
        safe_token = uuid.uuid4().hex[:12]
        timestamp = int(time.time())
        # Clean basename for prefix (alphanumeric and dashes only)
        base = os.path.splitext(os.path.basename(original_filename.replace("\0", "")))[0]
        sanitized_base = re.sub(r"[^a-zA-Z0-9_-]", "_", base)[:24].strip("_") or "resume"
        return f"{sanitized_base}_{timestamp}_{safe_token}.pdf"

    def get_safe_path(self, filename_or_id: str) -> Path:
        """
        Resolves a filename or ID strictly within the temporary directory.
        Raises FileValidationError on path traversal or invalid names.
        """
        if not filename_or_id or not str(filename_or_id).strip():
            raise FileValidationError("Filename or resume ID cannot be empty.", status_code=400)

        cleaned = str(filename_or_id).replace("\0", "").strip()
        safe_name = os.path.basename(cleaned)
        if not safe_name or safe_name in (".", ".."):
            raise FileValidationError("Invalid filename identifier.", status_code=400)

        if not safe_name.endswith(".pdf"):
            safe_name = f"{safe_name}.pdf"

        target_path = (self.temp_dir / safe_name).resolve()
        base_path = self.temp_dir.resolve()

        # Strict containment check
        try:
            target_path.relative_to(base_path)
        except ValueError:
            logger.error("Path traversal attempt detected: '%s'", filename_or_id)
            raise FileValidationError("Access denied: invalid file path.", status_code=403)

        return target_path

    def save_temporarily(self, content: bytes, original_filename: str) -> Tuple[str, Path]:
        """
        Saves the validated bytes to temporary storage and returns (unique_filename, full_path).
        """
        safe_filename = self.generate_safe_filename(original_filename)
        destination_path = (self.temp_dir / safe_filename).resolve()

        with open(destination_path, "wb") as f:
            f.write(content)

        return safe_filename, destination_path

    def remove_file(self, filename: str) -> bool:
        """Removes a file from temporary storage safely."""
        try:
            target = self.get_safe_path(filename)
            if target.exists() and target.is_file():
                target.unlink()
                return True
        except Exception:
            return False
        return False


# Singleton instance
storage_service = StorageService()

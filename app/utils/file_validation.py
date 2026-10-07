import mimetypes
import os
import re
from pathlib import Path
from typing import Optional, Set, Tuple
from app.config.settings import settings

# Common file signatures (magic bytes)
MAGIC_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".docx": [b"PK\x03\x04"],
    ".xlsx": [b"PK\x03\x04"],
    ".webp": [b"RIFF"],
}

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to prevent path traversal, null bytes,
    and dangerous shell characters.
    """
    # Strip directory components
    clean_name = os.path.basename(filename)
    # Remove null bytes and control chars
    clean_name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", clean_name)
    # Strip dangerous path navigation
    clean_name = clean_name.replace("..", "").replace("/", "").replace("\\", "")
    # Allow only alphanumeric, dashes, underscores, dots, and spaces
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\. ]", "_", clean_name).strip()
    if not clean_name:
        clean_name = "unnamed_document"
    return clean_name


def validate_uploaded_file(
    filename: str, 
    content: bytes, 
    max_size_mb: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validates uploaded file size, extension, and content magic bytes.
    Returns: (is_valid, error_message)
    """
    max_bytes = (max_size_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    if len(content) > max_bytes:
        return False, f"File size ({len(content) / (1024*1024):.2f} MB) exceeds maximum allowed {settings.MAX_UPLOAD_SIZE_MB} MB"

    if len(content) == 0:
        return False, "Uploaded file is empty"

    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not permitted. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"

    # Check magic bytes if registered
    if ext in MAGIC_SIGNATURES:
        signatures = MAGIC_SIGNATURES[ext]
        matches = any(content.startswith(sig) for sig in signatures)
        if not matches:
            return False, f"File content does not match expected signature for '{ext}' format."

    # For text files, check if UTF-8/ASCII decodable
    if ext in [".txt", ".csv"]:
        try:
            content[:4096].decode("utf-8")
        except UnicodeDecodeError:
            try:
                content[:4096].decode("latin-1")
            except Exception:
                return False, f"File {filename} is not valid text/UTF-8 encoded."

    return True, None

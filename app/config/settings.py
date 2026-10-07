import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def load_dotenv_file(filepath: Path) -> None:
    """Lightweight .env loader without external dependency."""
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key not in os.environ:
                os.environ[key] = val

# Load .env if present
load_dotenv_file(BASE_DIR / ".env")


class Settings(BaseModel):
    # Application Info
    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "MultiMind AI"))
    APP_ENV: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    APP_HOST: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    APP_PORT: int = Field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True").lower() in ("true", "1", "yes"))
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "multimind-ai-super-secret-key-change-in-production-min32chars"))
    ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))

    # Database
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'multimind.db'}"))

    # LLM Settings
    LLM_PROVIDER: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "mock"))  # mock, openai, groq, gemini
    LLM_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    LLM_MODEL: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    LLM_TEMPERATURE: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.2")))
    LLM_MAX_TOKENS: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2048")))

    # Embeddings & Vector DB
    EMBEDDING_PROVIDER: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "mock"))  # mock, openai, sentence-transformers
    EMBEDDING_MODEL: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    EMBEDDING_DIM: int = Field(default_factory=lambda: int(os.getenv("EMBEDDING_DIM", "384")))
    VECTOR_DB_TYPE: str = Field(default_factory=lambda: os.getenv("VECTOR_DB_TYPE", "memory_chroma"))
    VECTOR_DB_PATH: str = Field(default_factory=lambda: os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "data" / "vector_store")))

    # RAG Settings
    CHUNK_SIZE: int = Field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "600")))
    CHUNK_OVERLAP: int = Field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100")))
    TOP_K: int = Field(default_factory=lambda: int(os.getenv("TOP_K", "4")))
    SIMILARITY_THRESHOLD: float = Field(default_factory=lambda: float(os.getenv("SIMILARITY_THRESHOLD", "0.35")))

    # Storage & Upload limits
    MAX_UPLOAD_SIZE_MB: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")))
    ALLOWED_EXTENSIONS: List[str] = Field(default_factory=lambda: [
        ext.strip().lower() for ext in os.getenv(
            "ALLOWED_EXTENSIONS", 
            ".pdf,.docx,.txt,.csv,.xlsx,.xls,.png,.jpg,.jpeg,.webp"
        ).split(",")
    ])
    UPLOAD_DIR: Path = Field(default_factory=lambda: BASE_DIR / "data" / "uploads")
    PROCESSED_DIR: Path = Field(default_factory=lambda: BASE_DIR / "data" / "processed")

    # Logging
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: Path = Field(default_factory=lambda: BASE_DIR / "data" / "multimind.log")

    model_config = {"arbitrary_types_allowed": True}


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
Path(settings.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

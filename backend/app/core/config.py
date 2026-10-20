"""
Core configuration and settings for the application.
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "AI Resume Parser & Job Matcher Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    # API Prefix
    API_V1_PREFIX: str = "/api"

    # Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    ]
    UPLOAD_TEMP_DIR: str = "/tmp/ai_resume_parser/resumes"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # OCR Configuration (Phase 4)
    OCR_ENABLED: bool = True
    OCR_MIN_CHARS_PER_PAGE: int = 50
    OCR_DPI: int = 200
    OCR_LANGUAGE: str = "eng"
    TESSERACT_CMD: Union[str, None] = None

    # LLM & Structured Extraction Configuration (Phase 9)
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", "mock"
    GEMINI_API_KEY: Union[str, None] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    OPENAI_API_KEY: Union[str, None] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_REPAIR_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: float = 45.0

    # Semantic Embeddings Configuration (Phase 16)
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_PROVIDER: str = "auto"  # "auto", "gemini", "mock"

    # JWT Authentication Configuration (Phase 18)
    JWT_SECRET_KEY: str = "ai_resume_parser_jwt_super_secret_key_production_grade_security_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # PostgreSQL Database Configuration (Phase 11)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_resume_parser"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()

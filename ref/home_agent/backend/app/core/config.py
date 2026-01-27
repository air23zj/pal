from typing import List, Union, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
import os
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Clarity"
    PROJECT_DESCRIPTION: str = "A modern AI-powered personal assistant"
    VERSION: str = "1.0.0"
    SHOW_API_DOCS: bool = True
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./clarity.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    DB_SSL_MODE: str = os.getenv("DB_SSL_MODE", "prefer")
    DB_SSL_CA: Optional[str] = os.getenv("DB_SSL_CA")
    DB_SSL_CERT: Optional[str] = os.getenv("DB_SSL_CERT")
    DB_SSL_KEY: Optional[str] = os.getenv("DB_SSL_KEY")
    DB_CONNECT_RETRIES: int = int(os.getenv("DB_CONNECT_RETRIES", "3"))
    DB_CONNECT_RETRY_DELAY: int = int(os.getenv("DB_CONNECT_RETRY_DELAY", "5"))
    DB_STATEMENT_TIMEOUT: int = int(os.getenv("DB_STATEMENT_TIMEOUT", "30"))  # seconds
    DB_MIGRATION_ENABLED: bool = os.getenv("DB_MIGRATION_ENABLED", "true").lower() == "true"
    DB_MIGRATION_DIR: str = os.getenv("DB_MIGRATION_DIR", "migrations")
    
    # Redis Cache
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    REDIS_SOCKET_KEEPALIVE: bool = os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true"
    REDIS_RETRY_ON_TIMEOUT: bool = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
    REDIS_RETRY_MAX_ATTEMPTS: int = int(os.getenv("REDIS_RETRY_MAX_ATTEMPTS", "3"))
    REDIS_RETRY_DELAY: int = int(os.getenv("REDIS_RETRY_DELAY", "1"))
    REDIS_HEALTH_CHECK_INTERVAL: int = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
    
    # Cache Settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_PREFIX: str = os.getenv("CACHE_PREFIX", "cache")
    CACHE_VERSION: str = os.getenv("CACHE_VERSION", "v1")
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))  # 5 minutes
    CACHE_KEY_PREFIX: str = os.getenv("CACHE_KEY_PREFIX", "clarity")
    CACHE_SERIALIZER: str = os.getenv("CACHE_SERIALIZER", "json")  # json or pickle
    CACHE_KEY_FUNCTION: str = os.getenv("CACHE_KEY_FUNCTION", "default")  # default or custom
    CACHE_NULL_VALUES: bool = os.getenv("CACHE_NULL_VALUES", "false").lower() == "true"
    CACHE_COMPRESSION_ENABLED: bool = os.getenv("CACHE_COMPRESSION_ENABLED", "false").lower() == "true"
    CACHE_COMPRESSION_THRESHOLD: int = int(os.getenv("CACHE_COMPRESSION_THRESHOLD", "1000"))  # bytes
    
    # Session
    SESSION_MAX_AGE: int = 86400  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",  # Frontend development server
        "http://localhost:3000",  # Alternative frontend port
    ]
    
    # Security Headers
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png",
        ".mp3", ".wav", ".mp4", ".avi", ".mov"
    ]
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-west-2")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "clarity-files")
    
    # External APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SERPER_SEARCH_API_KEY: str = os.getenv("SERPER_SEARCH_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # API Rate Limits
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    RATE_LIMIT_EXPIRY: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_FILE: str = "logs/clarity.log"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10 days"
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_CLOSE_TIMEOUT: int = 10  # seconds
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = 300  # 5 minutes
    HEALTH_CHECK_TIMEOUT: int = 5  # seconds
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 
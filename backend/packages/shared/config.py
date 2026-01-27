"""
Centralized configuration management for PAL.
Uses Pydantic settings for type safety and validation.
"""
import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum


def load_legacy_env_file():
    """
    Load environment variables from project root .env file.
    This provides a single, clean configuration location.
    """
    # Try to find the project root by walking up from the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up until we find a directory that contains both backend/ and .git or similar
    project_root = current_dir
    for _ in range(10):  # Prevent infinite loop
        if os.path.exists(os.path.join(project_root, 'backend')) and os.path.exists(os.path.join(project_root, 'README.md')):
            break
        parent = os.path.dirname(project_root)
        if parent == project_root:  # Reached root
            break
        project_root = parent

    # Load from project root .env file
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


# Load environment variables before creating settings
load_legacy_env_file()


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    GEMINI = "gemini"


class Settings(BaseSettings):
    """
    Application settings with validation and type safety.
    Loaded from environment variables with fallback defaults.
    """

    # ===========================================
    # CORE CONFIGURATION
    # ===========================================

    app_env: Environment = Field(default=Environment.DEVELOPMENT, env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ===========================================
    # LLM CONFIGURATION
    # ===========================================

    llm_provider: LLMProvider = Field(default=LLMProvider.LMSTUDIO, env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", env="LLM_MODEL")

    @property
    def effective_llm_model(self) -> str:
        """Get the effective model name based on the provider."""
        # If explicitly set via LLM_MODEL, use that
        if hasattr(self, '_llm_model') and self._llm_model:
            return self._llm_model

        # Otherwise use provider-specific defaults (user's preferred models)
        provider_defaults = {
            LLMProvider.GEMINI: "gemini-2.5-flash-lite",
            LLMProvider.CLAUDE: "claude-3-5-haiku",
            LLMProvider.OPENAI: "gpt-4o-mini",  # GPT-4o-mini (fastest & most cost-effective)
            LLMProvider.LMSTUDIO: "openai/gpt-oss-20b",
            LLMProvider.OLLAMA: "openai/gpt-oss-20b",
        }

        return provider_defaults.get(self.llm_provider, "gpt-4o-mini")
    llm_endpoint: Optional[str] = Field(default=None, env="LLM_ENDPOINT")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")

    # API Keys (sensitive - should be set via environment)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # ===========================================
    # EXTERNAL API KEYS
    # ===========================================

    serpapi_api_key: Optional[str] = Field(default=None)
    serper_search_api_key: Optional[str] = Field(default=None)
    news_api_key: Optional[str] = Field(default=None)
    gemini_api_key: Optional[str] = Field(default=None)
    openweather_api_key: Optional[str] = Field(default=None)

    # YouTube proxy settings for working around IP bans
    youtube_proxy_url: Optional[str] = Field(default=None, env="YOUTUBE_PROXY_URL")

    # ===========================================
    # DATABASE CONFIGURATION
    # ===========================================

    database_url: str = Field(default="sqlite:///./pal.db", env="DATABASE_URL")
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # ===========================================
    # INTEGRATION SERVICES
    # ===========================================

    # Google Workspace
    mcp_gmail_enabled: bool = Field(default=False, env="MCP_GMAIL_ENABLED")
    mcp_calendar_enabled: bool = Field(default=False, env="MCP_CALENDAR_ENABLED")
    mcp_tasks_enabled: bool = Field(default=False, env="MCP_TASKS_ENABLED")

    # Google API Credentials
    gmail_credentials_path: str = Field(default="credentials/gmail_credentials.json", env="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str = Field(default="credentials/gmail_token.json", env="GMAIL_TOKEN_PATH")
    calendar_credentials_path: str = Field(default="credentials/calendar_credentials.json", env="CALENDAR_CREDENTIALS_PATH")
    calendar_token_path: str = Field(default="credentials/calendar_token.json", env="CALENDAR_TOKEN_PATH")
    tasks_credentials_path: str = Field(default="credentials/tasks_credentials.json", env="TASKS_CREDENTIALS_PATH")
    tasks_token_path: str = Field(default="credentials/tasks_token.json", env="TASKS_TOKEN_PATH")

    # ===========================================
    # APPLICATION SETTINGS
    # ===========================================

    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    cors_origins_str: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    session_timeout_minutes: int = Field(default=480, env="SESSION_TIMEOUT_MINUTES")

    # ===========================================
    # FEATURE FLAGS
    # ===========================================

    # Core Features
    enable_brief_generation: bool = Field(default=True, env="ENABLE_BRIEF_GENERATION")
    enable_settings_api: bool = Field(default=True, env="ENABLE_SETTINGS_API")

    # Lifestyle Modules
    enable_flights: bool = Field(default=True, env="ENABLE_FLIGHTS")
    enable_dining: bool = Field(default=True, env="ENABLE_DINING")
    enable_travel: bool = Field(default=True, env="ENABLE_TRAVEL")
    enable_local: bool = Field(default=True, env="ENABLE_LOCAL")
    enable_shopping: bool = Field(default=True, env="ENABLE_SHOPPING")

    # Communication Modules
    enable_gmail: bool = Field(default=False, env="ENABLE_GMAIL")
    enable_calendar: bool = Field(default=False, env="ENABLE_CALENDAR")
    enable_tasks: bool = Field(default=False, env="ENABLE_TASKS")

    # Research Modules
    enable_news: bool = Field(default=True, env="ENABLE_NEWS")
    enable_research: bool = Field(default=True, env="ENABLE_RESEARCH")

    # AI Features
    enable_search_summarization: bool = Field(default=True, env="ENABLE_SEARCH_SUMMARIZATION")
    enable_youtube_summarization: bool = Field(default=True, env="ENABLE_YOUTUBE_SUMMARIZATION")

    # ===========================================
    # PERFORMANCE & LIMITS
    # ===========================================

    search_requests_per_minute: int = Field(default=30, env="SEARCH_REQUESTS_PER_MINUTE")
    youtube_requests_per_minute: int = Field(default=10, env="YOUTUBE_REQUESTS_PER_MINUTE")
    brief_generation_timeout_seconds: int = Field(default=300, env="BRIEF_GENERATION_TIMEOUT_SECONDS")

    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    weather_cache_ttl_seconds: int = Field(default=600, env="WEATHER_CACHE_TTL_SECONDS")

    # ===========================================
    # MONITORING & ANALYTICS
    # ===========================================

    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    posthog_api_key: Optional[str] = Field(default=None, env="POSTHOG_API_KEY")

    # ===========================================
    # DEVELOPMENT SETTINGS
    # ===========================================

    reload: bool = Field(default=True, env="RELOAD")
    use_mock_data: bool = Field(default=False, env="USE_MOCK_DATA")
    debug_sql: bool = Field(default=False, env="DEBUG_SQL")
    debug_api_calls: bool = Field(default=False, env="DEBUG_API_CALLS")

    # ===========================================
    # VALIDATORS
    # ===========================================


    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not (v.startswith('sqlite://') or v.startswith('postgresql://')):
            raise ValueError("DATABASE_URL must be SQLite or PostgreSQL")
        return v

    @validator('llm_provider')
    def validate_llm_provider(cls, v, values):
        """Validate LLM provider and ensure required API keys are present."""
        provider = LLMProvider(v)
        app_env = values.get('app_env', Environment.DEVELOPMENT)

        # In development, allow dummy/placeholder keys for testing
        is_dev = app_env == Environment.DEVELOPMENT

        if provider == LLMProvider.OPENAI:
            api_key = values.get('openai_api_key')
            if not is_dev and (not api_key or api_key == "lm-studio-dummy-key" or api_key == "your_openai_key_here"):
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai' in production")
        elif provider == LLMProvider.CLAUDE:
            api_key = values.get('anthropic_api_key')
            if not is_dev and (not api_key or api_key == "your_anthropic_key_here"):
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'claude' in production")
        elif provider == LLMProvider.GEMINI:
            api_key = values.get('gemini_api_key')
            if not is_dev and (not api_key or api_key == "your_gemini_key_here"):
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini' in production")

        return provider

    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        """Warn about insecure secret keys in production."""
        if values.get('app_env') == Environment.PRODUCTION and v == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from default in production")
        return v

    # ===========================================
    # UTILITY METHODS
    # ===========================================

    def get_llm_api_key(self) -> Optional[str]:
        """Get the appropriate LLM API key based on provider."""
        if self.llm_provider == LLMProvider.OPENAI:
            return self.openai_api_key
        elif self.llm_provider == LLMProvider.CLAUDE:
            return self.anthropic_api_key
        elif self.llm_provider == LLMProvider.GEMINI:
            return self.gemini_api_key
        return None

    def get_search_api_key(self) -> Optional[str]:
        """Get the best available search API key."""
        return self.serpapi_api_key or self.serper_search_api_key

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list, parsed from the string."""
        cors_str = getattr(self, '_cors_origins_str', "http://localhost:3000,http://127.0.0.1:3000")
        return [origin.strip() for origin in cors_str.split(',') if origin.strip()]

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == Environment.DEVELOPMENT

    class Config:
        """Pydantic configuration."""
        # Disable all automatic environment loading since we handle it manually
        env_file = None
        env_prefix = ''
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Load environment variables before creating settings
load_legacy_env_file()

# Global settings instance
settings = Settings()

# Manually populate settings from environment variables for fields that need it
def populate_from_env():
    """Manually populate settings from environment variables."""
    # Simple string/number fields
    string_fields = [
        'llm_endpoint', 'ollama_base_url', 'openai_api_key', 'anthropic_api_key',
        'serpapi_api_key', 'serper_search_api_key', 'news_api_key', 'gemini_api_key',
        'openweather_api_key', 'database_url', 'qdrant_url', 'redis_url', 'secret_key',
        'sentry_dsn', 'posthog_api_key', 'log_level'
    ]

    for field in string_fields:
        env_value = os.getenv(field.upper())
        if env_value is not None:
            setattr(settings, field, env_value)

    # Handle llm_model specially - store explicitly set value
    llm_model_env = os.getenv('LLM_MODEL')
    if llm_model_env is not None:
        settings._llm_model = llm_model_env

    # Boolean fields
    bool_fields = [
        'debug', 'mcp_gmail_enabled', 'mcp_calendar_enabled', 'mcp_tasks_enabled',
        'enable_brief_generation', 'enable_settings_api', 'enable_flights', 'enable_dining',
        'enable_travel', 'enable_local', 'enable_shopping', 'enable_news', 'enable_research',
        'enable_search_summarization', 'enable_youtube_summarization', 'reload', 'use_mock_data',
        'debug_sql', 'debug_api_calls'
    ]

    for field in bool_fields:
        env_value = os.getenv(field.upper())
        if env_value is not None:
            setattr(settings, field, env_value.lower() in ('true', '1', 'yes', 'on'))

    # Integer fields
    int_fields = [
        'port', 'session_timeout_minutes', 'search_requests_per_minute', 'youtube_requests_per_minute',
        'brief_generation_timeout_seconds', 'cache_ttl_seconds', 'weather_cache_ttl_seconds'
    ]

    for field in int_fields:
        env_value = os.getenv(field.upper())
        if env_value is not None:
            try:
                setattr(settings, field, int(env_value))
            except ValueError:
                pass  # Keep default

    # Store cors_origins_str for later use
    settings._cors_origins_str = os.getenv('CORS_ORIGINS', "http://localhost:3000,http://127.0.0.1:3000")

    # Environment enum
    app_env = os.getenv('APP_ENV', 'development')
    if app_env in ['development', 'staging', 'production']:
        settings.app_env = Environment(app_env)

    # LLM provider enum
    llm_provider = os.getenv('LLM_PROVIDER', 'openai')
    if llm_provider in ['openai', 'claude', 'ollama', 'lmstudio']:
        settings.llm_provider = LLMProvider(llm_provider)

# Populate settings from environment
populate_from_env()
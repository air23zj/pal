"""
Morning Brief AGI - FastAPI Backend
Main API server entry point
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import brief, feedback, health, settings as settings_router, summarization
from packages.shared.config import settings as config

# Set up logging based on configuration
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables from project root .env file
def load_env_file():
    """
    Load environment variables from project root .env file.
    """
    # Get the project root (parent of backend directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # Load from project root .env file
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        logger.info(f"Loading environment from: {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    else:
        logger.warning(f"No .env file found at: {env_path}")
        logger.warning("Create .env file from .env.example template")

# Load environment variables
load_env_file()

# Validate critical configuration
if not config.get_llm_api_key() and not config.use_mock_data:
    logger.warning("No LLM API key configured. AI features will use mock responses.")

if not config.get_search_api_key():
    logger.warning("No search API key configured. Search features will be limited.")

logger.info(f"Application starting in {config.app_env.value} mode")
logger.info(f"LLM Provider: {config.llm_provider.value}")
logger.info(f"Database: {config.database_url.split('://')[0]}")


# CORS configuration from environment
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Morning Brief API starting up...")
    yield
    # Shutdown
    print("👋 Morning Brief API shutting down...")


app = FastAPI(
    title="Morning Brief AGI API",
    description="Intelligent morning briefing system API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(brief.router, prefix="/api/brief", tags=["brief"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(summarization.router, prefix="/api", tags=["summarization"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Morning Brief AGI API",
        "version": "0.1.0",
        "status": "running",
    }

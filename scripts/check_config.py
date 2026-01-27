#!/usr/bin/env python3
"""
PAL Configuration Validator
Checks if all required environment variables and dependencies are properly configured.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from packages.shared.config import settings
except ImportError as e:
    print("❌ Failed to import configuration module:", e)
    sys.exit(1)


def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (not found)")
        return False


def check_service_running(url: str, service_name: str) -> bool:
    """Check if a web service is running."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name}: {url}")
            return True
        else:
            print(f"⚠️  {service_name}: {url} (status: {response.status_code})")
            return False
    except Exception:
        print(f"❌ {service_name}: {url} (not reachable)")
        return False


def check_command_available(command: str, description: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        print(f"✅ {description}: {command}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {description}: {command} (not found)")
        return False


def main():
    """Run all configuration checks."""
    print("🔍 PAL Configuration Check")
    print("=" * 50)

    all_good = True

    # Check environment
    print("\n📋 Environment:")
    print(f"   APP_ENV: {settings.app_env.value}")
    print(f"   DEBUG: {settings.debug}")
    print(f"   LOG_LEVEL: {settings.log_level}")

    # Check LLM configuration
    print("\n🤖 LLM Configuration:")
    print(f"   Provider: {settings.llm_provider.value}")
    print(f"   Model: {settings.llm_model}")

    if settings.llm_provider.value == "openai":
        if settings.openai_api_key and settings.openai_api_key != "lm-studio-dummy-key":
            print("   ✅ OpenAI API key configured")
        else:
            print("   ⚠️  OpenAI API key not configured or using dummy key")
            if settings.llm_endpoint:
                print(f"   Checking LM Studio at: {settings.llm_endpoint}")
                check_service_running(f"{settings.llm_endpoint}/models", "LM Studio")
    elif settings.llm_provider.value == "ollama":
        print(f"   Checking Ollama at: {settings.ollama_base_url}")
        check_service_running(f"{settings.ollama_base_url}/api/tags", "Ollama")

    # Check external APIs
    print("\n🔍 External APIs:")
    if settings.get_search_api_key():
        print("   ✅ Search API key configured")
    else:
        print("   ❌ Search API key not configured")
        all_good = False

    # Check database
    print("\n💾 Database:")
    if settings.database_url.startswith("sqlite://"):
        db_path = settings.database_url.replace("sqlite:///", "")
        check_file_exists(db_path, "SQLite database")
    elif settings.database_url.startswith("postgresql://"):
        print(f"   📡 PostgreSQL: {settings.database_url.split('@')[1].split('/')[0]}")

    # Check services
    print("\n🌐 Services:")
    check_service_running(f"{settings.qdrant_url}/healthz", "Qdrant")

    if settings.redis_url:
        # Redis check would require redis-py
        print(f"   📡 Redis: {settings.redis_url}")

    # Check feature flags
    print("\n⚙️  Enabled Features:")
    features = [
        ("Brief Generation", settings.enable_brief_generation),
        ("Settings API", settings.enable_settings_api),
        ("Flights", settings.enable_flights),
        ("Dining", settings.enable_dining),
        ("Travel", settings.enable_travel),
        ("Local", settings.enable_local),
        ("Shopping", settings.enable_shopping),
        ("News", settings.enable_news),
        ("Research", settings.enable_research),
        ("Search Summarization", settings.enable_search_summarization),
        ("YouTube Summarization", settings.enable_youtube_summarization),
    ]

    for feature, enabled in features:
        status = "✅" if enabled else "❌"
        print(f"   {status} {feature}")

    # Check development tools
    print("\n🛠️  Development Tools:")
    check_command_available("python", "Python")
    check_command_available("node", "Node.js")
    check_command_available("npm", "npm")

    # Final status
    print("\n" + "=" * 50)
    if all_good:
        print("✅ Configuration looks good!")
        print("\n🚀 You can now run: ./scripts/launch.sh")
    else:
        print("⚠️  Some configuration issues found.")
        print("   Please check the errors above and update your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
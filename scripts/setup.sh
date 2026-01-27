#!/bin/bash
set -e

echo "🚀 Setting up Morning Brief AGI..."
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }
echo "✅ Docker and Docker Compose found"
echo ""

# Create env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Morning Brief AGI - Environment Configuration

# Runtime Configuration
SANDBOX_PROVIDER=open-skills
SANDBOX_ENDPOINT=http://localhost:8222

# LLM Configuration
LLM_PROVIDER=ollama
LLM_ENDPOINT=http://localhost:11434
LLM_MODEL=llama3.2
LLM_API_KEY=

# Database
DATABASE_URL=postgresql://morning_brief:dev_password@postgres:5432/morning_brief

# Redis
REDIS_URL=redis://redis:6379/0

# MCP Servers
MCP_GMAIL_ENABLED=false
MCP_CALENDAR_ENABLED=false
MCP_TASKS_ENABLED=false

# Application
APP_ENV=development
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env"
else
    echo "ℹ️  .env already exists, skipping"
fi
echo ""

# Create frontend env file if it doesn't exist
if [ ! -f frontend/.env.local ]; then
    echo "Creating frontend/.env.local file..."
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env.local"
else
    echo "ℹ️  frontend/.env.local already exists, skipping"
fi
echo ""

# Pull Docker images
echo "Pulling Docker images..."
docker-compose pull
echo "✅ Images pulled"
echo ""

# Build services
echo "Building services..."
docker-compose build
echo "✅ Services built"
echo ""

# Start services
echo "Starting services..."
docker-compose up -d
echo "✅ Services started"
echo ""

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 5

# Initialize database
echo "Initializing database..."
docker-compose exec -T backend python scripts/init_db.py || echo "⚠️  Database initialization failed (may already be initialized)"
echo ""

# Check health
echo "Checking service health..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed (may still be starting up)"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "⚠️  Frontend not yet accessible (may still be starting up)"
fi
echo ""

echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   All:       docker-compose logs -f"
echo "   Backend:   docker-compose logs -f backend"
echo "   Frontend:  docker-compose logs -f frontend"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"
echo ""
echo "📚 See README.md for more information"
echo "=================================================="

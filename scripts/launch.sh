#!/bin/bash
set -e

echo "🚀 Launching PAL (Morning Brief AGI) with LM Studio..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check configuration and dependencies
print_status "Checking configuration..."

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env not found. Creating from template..."
    cp .env.example .env
    print_warning "Please edit .env with your API keys and settings"
    echo ""
fi

# Check for required API keys based on configuration
if grep -q "LLM_PROVIDER=openai" .env 2>/dev/null; then
    if grep -q "OPENAI_API_KEY=lm-studio-dummy-key" .env 2>/dev/null; then
        print_warning "Using LM Studio dummy key. Checking if LM Studio is running..."
        if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
            MODEL_NAME=$(curl -s http://localhost:1234/v1/models | jq -r '.data[0].id' 2>/dev/null || echo "unknown")
            print_success "LM Studio is running with model: $MODEL_NAME"
        else
            print_error "LM Studio is not running!"
            echo ""
            echo "Please start LM Studio and load a model first:"
            echo "1. Open LM Studio application"
            echo "2. Go to 'My Models' tab and download a model (e.g., llama-3.2-3b-instruct)"
            echo "3. Go to 'Local Server' tab"
            echo "4. Select your model and click 'Start Server'"
            echo "5. Verify server is running at http://localhost:1234"
            echo ""
            exit 1
        fi
    else
        print_success "OpenAI API key configured"
    fi
elif grep -q "LLM_PROVIDER=ollama" .env 2>/dev/null; then
    print_status "Checking Ollama..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama is running"
    else
        print_warning "Ollama not detected. Make sure it's running: 'ollama serve'"
    fi
elif grep -q "LLM_PROVIDER=lmstudio" .env 2>/dev/null; then
    print_status "Checking LM Studio..."
    if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
        MODEL_NAME=$(curl -s http://localhost:1234/v1/models | jq -r '.data[0].id' 2>/dev/null || echo "unknown")
        print_success "LM Studio is running with model: $MODEL_NAME"
    else
        print_warning "LM Studio not detected. Make sure LM Studio is running on localhost:1234"
        echo ""
        echo "To start LM Studio:"
        echo "1. Open LM Studio application"
        echo "2. Go to 'Local Server' tab"
        echo "3. Select your model and click 'Start Server'"
        echo "4. Verify server is running at http://localhost:1234"
        echo ""
    fi
else
    print_warning "No LLM provider configured. AI features will use mock responses."
fi

# Check for search API keys
if grep -q "SERPAPI_API_KEY=your_serpapi_key_here" .env 2>/dev/null; then
    print_warning "SerpApi key not configured. Search features will be limited."
else
    print_success "SerpApi key configured"
fi

echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop any existing processes
print_status "Stopping any existing PAL processes..."
pkill -f "uvicorn.*apps.api.main" 2>/dev/null || true
pkill -f "next.*dev" 2>/dev/null || true
sleep 2
print_success "Cleaned up existing processes"
echo ""

# Load environment variables
if [ -f .env ]; then
    print_status "Loading environment variables..."
    source .env
    print_success "Environment variables loaded from .env"
elif [ -f config/api_keys.env ]; then
    print_status "Loading API keys from config (legacy)..."
    source config/api_keys.env
    print_success "API keys loaded from config/api_keys.env"
else
    print_warning "No environment configuration found."
    print_warning "Create .env with your environment variables."
    print_warning "See .env.example for the required variables."
fi

# Start backend server
print_status "Starting backend server..."
cd backend
if python -c "import uvicorn; print('uvicorn available')" 2>/dev/null; then
    nohup env SERPAPI_API_KEY="$SERPAPI_API_KEY" uvicorn apps.api.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    print_success "Backend server started (PID: $BACKEND_PID)"
else
    print_error "uvicorn not available. Please install dependencies:"
    echo "  cd backend && pip install -r requirements.txt"
    exit 1
fi
cd ..
echo ""

# Wait for backend to start
print_status "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        print_success "Backend is ready at http://localhost:8000"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    print_error "Backend failed to start properly. Check logs:"
    echo "  tail -f logs/backend.log"
    exit 1
fi
echo ""

# Start frontend server
print_status "Starting frontend server..."
cd frontend
if [ -f "package.json" ] && grep -q '"next"' package.json; then
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    print_success "Frontend server started (PID: $FRONTEND_PID)"
else
    print_error "Frontend dependencies not installed. Please run:"
    echo "  cd frontend && npm install"
    exit 1
fi
cd ..
echo ""

# Wait for frontend to start
print_status "Waiting for frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is ready at http://localhost:3000"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_warning "Frontend may still be starting up. Check logs:"
    echo "  tail -f logs/frontend.log"
fi
echo ""

# Test LLM integration
print_status "Testing LLM integration..."
if python -c "
import os
import sys
import asyncio
sys.path.insert(0, 'backend')

# Load environment variables
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

from packages.editor.llm_client import get_llm_client

async def test():
    try:
        client = get_llm_client()
        if client.is_available():
            response = await client.generate('Test connection')
            return len(response) > 0
        return False
    except:
        return False

result = asyncio.run(test())
print('✅' if result else '❌')
" 2>/dev/null | grep -q "✅"; then
    print_success "LLM integration working"
else
    print_warning "LLM integration may have issues. Check LM Studio connection."
fi
echo ""

# Open browser
print_status "Opening browser..."
if command -v open >/dev/null 2>&1; then
    open http://localhost:3000
    print_success "Browser opened to http://localhost:3000"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:3000
    print_success "Browser opened to http://localhost:3000"
else
    print_warning "Could not automatically open browser"
fi
echo ""

# Final status
echo "=================================================="
print_success "PAL Launch Complete!"
echo ""
echo "🌐 Access your application:"
echo "   Dashboard:  http://localhost:3000"
echo "   API:        http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo ""
echo "📊 Process IDs:"
if [ -f backend.pid ]; then
    echo "   Backend:    $(cat backend.pid)"
fi
if [ -f frontend.pid ]; then
    echo "   Frontend:   $(cat frontend.pid)"
fi
echo ""
echo "📝 Logs:"
echo "   Backend:    logs/backend.log"
echo "   Frontend:   logs/frontend.log"
echo ""
echo "🛑 To stop:"
echo "   ./scripts/stop.sh"
echo "   or kill $(cat backend.pid 2>/dev/null) $(cat frontend.pid 2>/dev/null)"
echo ""
echo "📚 See README.md for more information"
echo "=================================================="

# Save PIDs for easy stopping
echo "# PAL Process IDs - Generated $(date)" > pids.txt
echo "BACKEND_PID=$BACKEND_PID" >> pids.txt
echo "FRONTEND_PID=$FRONTEND_PID" >> pids.txt
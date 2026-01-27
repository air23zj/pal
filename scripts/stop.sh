#!/bin/bash

echo "🛑 Stopping PAL (Morning Brief AGI)..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop processes using PIDs if available
if [ -f pids.txt ]; then
    print_status "Stopping processes from pids.txt..."
    source pids.txt
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true
        print_success "Backend stopped (PID: $BACKEND_PID)"
    else
        print_status "Backend already stopped"
    fi

    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend stopped (PID: $FRONTEND_PID)"
    else
        print_status "Frontend already stopped"
    fi

    rm -f pids.txt backend.pid frontend.pid
else
    print_status "Stopping all PAL processes..."
    # Kill by process name
    pkill -f "uvicorn.*apps.api.main" 2>/dev/null || true
    pkill -f "next.*dev" 2>/dev/null || true

    # Also kill any remaining processes
    pkill -f "node.*next" 2>/dev/null || true
    pkill -f "python.*uvicorn" 2>/dev/null || true

    print_success "All PAL processes stopped"
fi

# Clean up any remaining processes on ports
print_status "Checking for processes on PAL ports..."

# Check port 8000 (backend)
if lsof -i :8000 >/dev/null 2>&1; then
    print_status "Found process on port 8000, stopping..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    print_success "Port 8000 cleared"
fi

# Check port 3000 (frontend)
if lsof -i :3000 >/dev/null 2>&1; then
    print_status "Found process on port 3000, stopping..."
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    print_success "Port 3000 cleared"
fi

echo ""
print_success "PAL stopped successfully!"
echo ""
echo "💡 To restart: ./scripts/launch.sh"
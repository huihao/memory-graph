#!/bin/bash

# Memory Graph - Quick Start Script
# This script helps you start all components of the Memory Graph system

echo "================================================"
echo "Memory Graph - Quick Start"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in the correct directory
if [ ! -d "backend" ] || [ ! -d "frontend" ] || [ ! -d "browser-extension" ]; then
    echo -e "${RED}Error: Please run this script from the memory-graph root directory${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3 && ! command_exists python; then
    echo -e "${RED}✗ Python is not installed${NC}"
    echo "  Please install Python 3.8 or higher"
    exit 1
fi
echo -e "${GREEN}✓ Python is installed${NC}"

if ! command_exists npm; then
    echo -e "${YELLOW}⚠ npm is not installed${NC}"
    echo "  Frontend will not be available. Install Node.js to enable frontend."
    SKIP_FRONTEND=1
else
    echo -e "${GREEN}✓ npm is installed${NC}"
fi

echo ""
echo "================================================"
echo "Starting Backend Server"
echo "================================================"

# Check if backend dependencies are installed
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv 2>/dev/null || python -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

echo "Installing/updating dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}Starting backend server at http://localhost:8000${NC}"
echo "Press Ctrl+C to stop all services"
echo ""

# Start backend in background
python main.py &
BACKEND_PID=$!

# Give backend time to start
sleep 3

cd ..

# Start frontend if npm is available
if [ -z "$SKIP_FRONTEND" ]; then
    echo ""
    echo "================================================"
    echo "Starting Frontend"
    echo "================================================"
    
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies (this may take a while)..."
        npm install
    fi
    
    echo -e "${GREEN}Starting frontend at http://localhost:3000${NC}"
    echo ""
    
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
fi

echo ""
echo "================================================"
echo "Services Started!"
echo "================================================"
echo -e "${GREEN}✓ Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}✓ API Docs:${NC} http://localhost:8000/docs"

if [ -z "$SKIP_FRONTEND" ]; then
    echo -e "${GREEN}✓ Frontend:${NC} http://localhost:3000"
fi

echo ""
echo "Next steps:"
echo "1. Install the browser extension from the 'browser-extension' directory"
echo "2. Configure the extension to use http://localhost:8000"
echo "3. Click 'Process All Bookmarks' in the extension"
echo "4. View your articles at http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID 2>/dev/null; [ -n '$FRONTEND_PID' ] && kill $FRONTEND_PID 2>/dev/null; exit 0" INT

wait

#!/bin/bash

echo "========================================"
echo " REAL ESTATE AI ASSISTANT - QUICK START"
echo "========================================"
echo ""

# Check if in correct directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "ERROR: Run this from the real_estate_ai_assistant_v2 folder!"
    exit 1
fi

echo "Step 1: Starting Backend..."
cd backend

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    ../.tools/uv venv --python ../.python/cpython-3.12.13-macos-aarch64-none/bin/python3.12
    ../.tools/uv pip install --python .venv/bin/python -r requirements.txt
fi

source .venv/bin/activate

if [ ! -f "app.db" ]; then
    echo "Initializing database..."
    python -c "from app.db.session import engine, Base; Base.metadata.create_all(bind=engine)"
fi

echo "Starting FastAPI backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ..

echo ""
echo "Step 2: Starting Frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Starting Next.js frontend on port 3001..."
npm run dev -- --port 3001 &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo " READY!"
echo "========================================"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

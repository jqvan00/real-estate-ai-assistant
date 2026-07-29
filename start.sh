#!/bin/bash

# Real Estate AI Assistant - Start Script
# This script starts both the backend and frontend servers

echo "=========================================="
echo "Real Estate AI Assistant"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Must run this script from the real_estate_ai_assistant_v2 directory"
    exit 1
fi

# Kill any existing processes on ports 8000 and 3000
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null

echo ""
echo "Starting Backend Server..."
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/real-estate-backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "Backend PID: $BACKEND_PID"
echo "Backend Logs: /tmp/real-estate-backend.log"
echo ""

sleep 2

echo "Starting Frontend Server..."
cd frontend
npm run dev > /tmp/real-estate-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "Frontend PID: $FRONTEND_PID"
echo "Frontend Logs: /tmp/real-estate-frontend.log"
echo ""

sleep 5

echo "=========================================="
echo "Servers Started!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3001"
echo ""
echo "To view logs:"
echo "  Backend:  tail -f /tmp/real-estate-backend.log"
echo "  Frontend: tail -f /tmp/real-estate-frontend.log"
echo ""
echo "To stop servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=========================================="
echo ""
echo "Opening frontend in browser..."
sleep 2
open http://localhost:3001
echo ""
echo "Ready to search properties!"
echo ""

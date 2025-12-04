#!/bin/bash

# LLM Council - Start script

echo "Starting LLM Council..."
echo ""

# Load environment variables from .env if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Cleanup function to kill process trees
cleanup() {
  echo ""
  echo "Stopping LLM Council..."
  
  # Kill backend process tree
  if [ ! -z "$BACKEND_PID" ]; then
    echo "Stopping backend (PID $BACKEND_PID)..."
    # Kill the process group of the backend
    pkill -P $BACKEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
  fi

  # Kill frontend process tree
  if [ ! -z "$FRONTEND_PID" ]; then
    echo "Stopping frontend (PID $FRONTEND_PID)..."
    # Kill the process group of the frontend
    pkill -P $FRONTEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
  fi
  
  exit
}

# Trap signals
trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend on http://localhost:8001..."
uv run python -m backend.main &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ LLM Council is running!"
echo "  Backend:  http://localhost:8001"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait

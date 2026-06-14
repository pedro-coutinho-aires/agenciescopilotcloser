#!/bin/bash
# Start Agencies Copilot Closer — backend + frontend in one command

set -e

# Check .env
if [ ! -f backend/.env ]; then
  echo "Creating .env from template..."
  cp backend/.env.example backend/.env
  echo ""
  echo ">>> Edit backend/.env and add your ANTHROPIC_API_KEY, then run this script again."
  exit 1
fi

# Check if API key is set
if grep -q "your-anthropic-api-key-here" backend/.env; then
  echo ">>> Edit backend/.env and replace the placeholder with your real ANTHROPIC_API_KEY."
  exit 1
fi

echo "Starting Agencies Copilot Closer..."

# Backend
cd backend
if [ ! -d "venv" ]; then
  echo "Creating Python venv..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo "Starting backend on :8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend
cd frontend
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi
echo "Starting frontend on :3000..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "====================================="
echo "  Agencies Copilot Closer running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo "====================================="
echo ""
echo "Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait

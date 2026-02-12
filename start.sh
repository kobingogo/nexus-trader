#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping NEXUS Trader..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

echo "🚀 Starting NEXUS Trader..."

# Start Backend
echo "Starting Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi
python -m app.main &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ NEXUS Trader is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop."

wait $BACKEND_PID $FRONTEND_PID

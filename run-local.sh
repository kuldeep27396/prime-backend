#!/bin/bash

# PRIME Local Development Runner
echo "🚀 Starting PRIME locally..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start Backend
echo "🐍 Starting Backend (FastAPI)..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Start backend server
echo "🚀 Starting backend server on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Frontend
echo "⚛️  Starting Frontend (React + Vite)..."
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend server
echo "🚀 Starting frontend server on http://localhost:3000"
npm run dev -- --port 3000 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "🎉 PRIME is now running locally!"
echo ""
echo "📋 Services:"
echo "   🐍 Backend API:    http://localhost:8000"
echo "   📚 API Docs:       http://localhost:8000/docs"
echo "   ⚛️  Frontend:       http://localhost:3000"
echo ""
echo "🔧 To test the chatbot system:"
echo "   1. Visit http://localhost:3000"
echo "   2. Register/Login as a recruiter"
echo "   3. Create chatbot templates"
echo "   4. Test the pre-screening flow"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
wait
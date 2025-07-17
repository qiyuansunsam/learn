#!/bin/bash

# Customer Data Processing Pipeline - Automatic Startup Script

echo "🚀 Starting Customer Data Processing Pipeline..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.7+ first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 14+ first.${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Function to install backend dependencies
install_backend() {
    echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
    cd backend
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt not found in backend directory${NC}"
        exit 1
    fi
    
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install backend dependencies${NC}"
        exit 1
    fi
    cd ..
}

# Function to install frontend dependencies
install_frontend() {
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd frontend
    
    if [ ! -f "package.json" ]; then
        echo -e "${RED}❌ package.json not found in frontend directory${NC}"
        exit 1
    fi
    
    npm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend dependencies installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
    cd ..
}

# Function to start backend server
start_backend() {
    echo -e "${YELLOW}🔧 Starting backend server...${NC}"
    cd backend
    python app.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Check if backend is running
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Backend server started successfully (PID: $BACKEND_PID)${NC}"
        echo -e "${GREEN}📍 Backend running at: http://127.0.0.1:5001${NC}"
    else
        echo -e "${RED}❌ Failed to start backend server${NC}"
        exit 1
    fi
}

# Function to start frontend server
start_frontend() {
    echo -e "${YELLOW}🔧 Starting frontend development server...${NC}"
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # Wait a moment for frontend to start
    sleep 5
    
    # Check if frontend is running
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend server started successfully (PID: $FRONTEND_PID)${NC}"
        echo -e "${GREEN}📍 Frontend running at: http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Failed to start frontend server${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
}

# Function to handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Servers stopped successfully${NC}"
    exit 0
}

# Set up trap for cleanup on script exit
trap cleanup SIGINT SIGTERM

# Main execution
echo -e "${YELLOW}🔍 Checking for existing dependencies...${NC}"

# Check if backend dependencies need to be installed
if [ ! -d "backend/__pycache__" ] || [ ! -f "backend/uploads_log.db" ]; then
    install_backend
else
    echo -e "${GREEN}✅ Backend dependencies already installed${NC}"
fi

# Check if frontend dependencies need to be installed
if [ ! -d "frontend/node_modules" ]; then
    install_frontend
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

# Start servers
start_backend
start_frontend

echo -e "\n${GREEN}🎉 Customer Data Processing Pipeline is now running!${NC}"
echo -e "${GREEN}📱 Open your browser and navigate to: http://localhost:3000${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop both servers${NC}"

# Keep script running
while true; do
    sleep 1
done
# 🚀 Quick Start Guide

Get the NBA Performance Prediction System up and running in 5 minutes!

## Prerequisites

Before you begin, ensure you have:
- ✅ Python 3.8+ installed
- ✅ Node.js 14+ installed
- ✅ npm or yarn installed
- ✅ 500MB free disk space

## Option 1: Quick Start (Recommended)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd nba-probability-game

# Run the setup script
chmod +x setup.sh
./setup.sh
```

### 2. Start the Application

```bash
# Start backend (Terminal 1)
cd backend
source venv/bin/activate
python app.py

# Start frontend (Terminal 2)
cd frontend
npm start
```

### 3. Access the Application

Open your browser and go to:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api/health

## Option 2: Manual Setup

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
```

### Initialize Database

```bash
cd ../database
python init_db.py
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
```

### Start Services

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2 - Frontend
cd frontend
npm start
```

## Option 3: Docker (Easiest)

```bash
# Build and start all services
docker-compose up --build

# Access at:
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

## First Steps

### 1. Make Your First Prediction

1. Open http://localhost:3000
2. Select a player (e.g., "LeBron James")
3. Choose an opponent team (e.g., "BOS")
4. Set the game date
5. Click "Get Prediction"

### 2. Compare Players

1. Switch to "Compare Players" mode
2. Select two players
3. Choose opponent and date
4. Click "Compare Players"

### 3. API Test

```bash
# Test the API
curl http://localhost:5000/api/health

# Get players list
curl http://localhost:5000/api/players
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Module Not Found

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### Database Not Found

```bash
cd database
python init_db.py
```

### CORS Errors

Make sure both backend and frontend are running on the correct ports:
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

## What's Next?

- 📖 Read the full [README.md](README.md)
- 🔧 Configure settings in `.env` files
- 📊 Explore the [API Documentation](docs/API.md)
- 🎨 Customize the frontend
- 🤖 Train custom ML models

## Common Commands

```bash
# Backend
cd backend
source venv/bin/activate
python app.py                    # Start server
pytest                           # Run tests
python -m flake8                 # Lint code

# Frontend
cd frontend
npm start                        # Development server
npm run build                    # Production build
npm test                         # Run tests
npm run lint                     # Lint code

# Database
cd database
python init_db.py                # Initialize DB
sqlite3 nba_data.db              # Access DB directly

# Docker
docker-compose up                # Start all services
docker-compose down              # Stop all services
docker-compose logs -f           # View logs
docker-compose build             # Rebuild images
```

## System Check

Run this to verify everything is working:

```bash
# Backend health check
curl http://localhost:5000/api/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}

# Frontend check
curl http://localhost:3000

# Should return HTML
```

## Need Help?

- 📝 Check [README.md](README.md) for detailed documentation
- 🐛 Report issues on GitHub
- 💬 Read the [API Documentation](docs/API.md)
- 🔍 Search existing issues first

## Quick Reference

### Environment Variables

**Backend (.env)**
```env
FLASK_ENV=development
PORT=5000
DATABASE_PATH=../database/nba_data.db
```

**Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:5000/api
```

### Default Ports

- Frontend: 3000
- Backend: 5000
- Database: SQLite (file-based)

### Directory Structure

```
nba-probability-game/
├── backend/       # Flask API & ML models
├── frontend/      # React application
├── database/      # SQLite database & scripts
├── docs/          # Documentation
└── README.md      # Main documentation
```

---

**🎉 You're all set! Start making predictions and enjoy the system!**

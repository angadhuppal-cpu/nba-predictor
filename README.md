# NBA Player Predictor

AI-Powered NBA Player Performance Prediction System with Real-Time Statistics

## 🏀 Overview

A full-stack web application that predicts NBA player performance using machine learning, historical data, and comprehensive team statistics from the official NBA API.

## ✨ Features

- **AI-Powered Predictions**: Multi-factor algorithm using 29+ variables
- **Real-Time NBA Data**: Fetches live stats from official NBA Stats API
- **Comprehensive Analysis**: 
  - Historical matchup performance
  - Defensive matchup ratings
  - Opponent injury impact
  - Home/away adjustments
  - Player health factors
  - Recent form trends
  - Offensive environment impact
  - Shooting efficiency factors
- **Interactive UI**: React-based frontend with customizable prediction factors
- **Player Comparison**: Compare two players side-by-side
- **Historical Performance**: View past games vs specific opponents
- **Probability Calculations**: Statistical analysis with confidence intervals

## 🛠️ Tech Stack

### Backend
- **Python 3.13**
- **Flask** - REST API
- **SQLite** - Database
- **Pandas** - Data processing
- **NumPy** - Numerical computations
- **SciPy** - Statistical analysis
- **Scikit-learn** - Machine learning

### Frontend
- **React 18.2**
- **Tailwind CSS 3.4**
- **Fetch API** - HTTP requests

### Data Source
- **NBA Stats API** (stats.nba.com)
- Real-time team and player statistics

## 📊 Algorithm

Uses **7 prediction factors** with 29+ variables:

1. **Defensive Matchup** (DEF Rating + Pace + FG% Allowed)
2. **Opponent Injuries** (Key players out/doubtful)
3. **Home/Away** (Court advantage)
4. **Player Health** (Injury type impact)
5. **Recent Trends** (Form analysis)
6. **Offensive Environment** (Opponent offensive rating)
7. **Shooting Efficiency** (Opponent 3PT defense)

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 16+
- npm

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd nba-probability-game
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Fetch NBA Data**
```bash
python fetch_game_logs.py      # Fetch player game logs
python fetch_team_stats.py     # Fetch team statistics
```

4. **Frontend Setup**
```bash
cd ../frontend
npm install
```

5. **Run the Application**

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

6. **Access the App**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## 📁 Project Structure

```
nba-probability-game/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── advanced_predictor.py      # Prediction algorithm
│   ├── nba_predictor.py           # Basic predictor
│   ├── nba_data_pipeline.py       # Data fetching pipeline
│   ├── nba_data_fetcher.py        # NBA API client
│   ├── fetch_game_logs.py         # Game log scraper
│   ├── fetch_team_stats.py        # Team stats scraper
│   ├── team_stats_scheduler.py    # Auto-update scheduler
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js                 # Main React app
│   │   ├── components/
│   │   │   ├── PredictionForm.js
│   │   │   ├── PredictionResults.js
│   │   │   ├── PredictionVariables.js
│   │   │   ├── PredictionFactors.js
│   │   │   ├── HistoricalPerformance.js
│   │   │   └── ComparisonResults.js
│   │   └── services/
│   │       └── api.js             # API client
│   ├── package.json
│   └── tailwind.config.js
├── database/
│   ├── schema.sql                 # Database schema
│   └── nba_data.db               # SQLite database (generated)
├── docs/
│   ├── ALGORITHMS.md
│   ├── PREDICTION_VARIABLES.md
│   ├── TEAM_STATS_PIPELINE.md
│   └── ENHANCED_TEAM_STATS_INTEGRATION.md
└── README.md
```

## 🎯 API Endpoints

### Predictions
```bash
POST /api/predict
GET  /api/compare
GET  /api/history
```

### Data
```bash
GET /api/players
GET /api/teams
GET /api/team-stats
GET /api/injuries
```

### System
```bash
GET /api/health
GET /api/stats
```

## 📈 Data Pipeline

### Automated Updates
```bash
# Run scheduler (updates every 6 hours + daily at 4 AM)
python team_stats_scheduler.py
```

### Manual Updates
```bash
# Update team statistics
python fetch_team_stats.py

# Fetch player game logs
python fetch_game_logs.py

# Full data refresh
python nba_data_pipeline.py
```

## 🎨 Features in Detail

### 1. Single Player Prediction
- Select player and opponent
- Adjust custom prediction factors
- View historical matchup performance
- See probability distributions
- Confidence intervals

### 2. Player Comparison
- Compare two players vs same opponent
- Side-by-side statistics
- Fantasy point projections
- Recommendation engine

### 3. Customizable Factors
Users can adjust 5 prediction weights:
- Defensive Impact (0.5 - 1.5)
- Injury Boost (0.0 - 2.0)
- Home/Away Factor (0.5 - 1.5)
- Player Health (0.0 - 1.5)
- Trend Factor (0.5 - 1.5)

### 4. Prediction Variables Display
View all 29 variables used in calculations:
- Base historical data
- Defensive analysis metrics
- Opponent injury impacts
- Venue factors
- Health impacts
- Trend analysis
- Complete formula breakdown

## 📊 Database

**Schema includes:**
- `player_stats` - 12,505 game logs
- `player_season_stats` - 540 players
- `team_stats` - 30 teams with 25+ metrics
- `injury_report` - Current injuries
- `game_schedule` - Upcoming games
- `predictions_log` - Historical predictions

## 🔧 Configuration

### Environment Variables
```bash
PORT=5000
FLASK_ENV=development
```

### Database Location
```
../database/nba_data.db
```

## 📝 Documentation

Comprehensive documentation available in `/docs`:
- `ALGORITHMS.md` - Prediction algorithm details
- `PREDICTION_VARIABLES.md` - All 29 variables explained
- `TEAM_STATS_PIPELINE.md` - Team stats documentation
- `ENHANCED_TEAM_STATS_INTEGRATION.md` - Integration guide

## 🤝 Contributing

This is a personal project. Feel free to fork and modify for your own use.

## ⚠️ Disclaimer

**For entertainment and statistical analysis only.**
- Not financial advice
- Not gambling advice
- Always gamble responsibly
- Past performance doesn't guarantee future results

## 📜 License

MIT License - See LICENSE file for details

## 🎯 Project Stats

- **Total Lines of Code**: ~15,000+
- **Prediction Factors**: 7
- **Variables Evaluated**: 29
- **Players in Database**: 540
- **Game Logs**: 12,505
- **Teams**: 30 (all NBA teams)
- **API Endpoints**: 10+
- **Algorithm Version**: 3.1

## 🚀 Future Enhancements

- [ ] Machine learning model training on historical predictions
- [ ] Live game updates
- [ ] Mobile responsive design improvements
- [ ] User accounts and prediction history
- [ ] Social features (share predictions)
- [ ] Advanced analytics dashboard
- [ ] Integration with more data sources
- [ ] Real-time odds comparison

## 👨‍💻 Developer

Built with ❤️ using React, Flask, and the NBA Stats API

---

**Last Updated**: November 4, 2025
**Version**: 1.0.0

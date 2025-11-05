import React, { useState, useEffect } from 'react';
import './App.css';
import PredictionForm from './components/PredictionForm';
import PredictionResults from './components/PredictionResults';
import ComparisonResults from './components/ComparisonResults';
import HistoricalPerformance from './components/HistoricalPerformance';
import PredictionFactors from './components/PredictionFactors';
import PredictionVariables from './components/PredictionVariables';
import { fetchPlayers, fetchTeams, predictPerformance, comparePlayers } from './services/api';

function App() {
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [opponent, setOpponent] = useState('');
  const [gameDate, setGameDate] = useState(new Date().toISOString().split('T')[0]);
  const [isHome, setIsHome] = useState(true);
  const [injuryStatus, setInjuryStatus] = useState('healthy');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [compareMode, setCompareMode] = useState(false);
  const [player2, setPlayer2] = useState('');
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState(null);

  // Custom prediction factors
  const [customFactors, setCustomFactors] = useState({
    defensiveImpact: 1.0,
    injuryBoost: 1.0,
    homeAwayFactor: 1.0,
    playerInjuryFactor: 1.0,
    trendFactor: 1.0
  });

  useEffect(() => {
    // Fetch players and teams on component mount
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [playersData, teamsData] = await Promise.all([
        fetchPlayers(),
        fetchTeams()
      ]);
      setPlayers(playersData.players);
      setTeams(teamsData.teams);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load players and teams data');
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await predictPerformance({
        player: selectedPlayer,
        opponent,
        game_date: gameDate,
        is_home: isHome,
        injury_status: injuryStatus,
        custom_factors: customFactors
      });
      setPrediction(data);
      setComparison(null);
    } catch (err) {
      console.error('Error getting prediction:', err);
      setError(err.message || 'Failed to get prediction');
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await comparePlayers({
        player1: selectedPlayer,
        player2: player2,
        opponent,
        game_date: gameDate
      });
      setComparison(data);
      setPrediction(null);
    } catch (err) {
      console.error('Error comparing players:', err);
      setError(err.message || 'Failed to compare players');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (compareMode) {
      handleCompare();
    } else {
      handlePredict();
    }
  };

  const isFormValid = () => {
    if (!selectedPlayer || !opponent) return false;
    if (compareMode && !player2) return false;
    return true;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
            🏀 NBA Performance Predictor
          </h1>
          <p className="text-lg opacity-80">
            AI-Powered Player Performance Predictions
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-8 mb-8">
            <div className="flex justify-center mb-6">
              <button
                onClick={() => {
                  setCompareMode(false);
                  setPrediction(null);
                  setComparison(null);
                }}
                className={`px-6 py-2 rounded-l-lg transition-colors ${
                  !compareMode ? 'bg-orange-500' : 'bg-gray-600 hover:bg-gray-500'
                }`}
              >
                Single Prediction
              </button>
              <button
                onClick={() => {
                  setCompareMode(true);
                  setPrediction(null);
                  setComparison(null);
                }}
                className={`px-6 py-2 rounded-r-lg transition-colors ${
                  compareMode ? 'bg-orange-500' : 'bg-gray-600 hover:bg-gray-500'
                }`}
              >
                Compare Players
              </button>
            </div>

            <PredictionForm
              selectedPlayer={selectedPlayer}
              setSelectedPlayer={setSelectedPlayer}
              opponent={opponent}
              setOpponent={setOpponent}
              gameDate={gameDate}
              setGameDate={setGameDate}
              isHome={isHome}
              setIsHome={setIsHome}
              injuryStatus={injuryStatus}
              setInjuryStatus={setInjuryStatus}
              player2={player2}
              setPlayer2={setPlayer2}
              players={players}
              teams={teams}
              compareMode={compareMode}
            />

            {error && (
              <div className="mb-4 p-4 bg-red-500/20 border border-red-500 rounded-lg">
                <p className="text-red-200">{error}</p>
              </div>
            )}

            {/* Show historical performance when player and opponent are selected */}
            {!compareMode && selectedPlayer && opponent && (
              <HistoricalPerformance
                player={selectedPlayer}
                opponent={opponent}
              />
            )}

            {/* Show prediction factors control (only in single prediction mode) */}
            {!compareMode && (
              <PredictionFactors
                factors={customFactors}
                setFactors={setCustomFactors}
                onReset={() => {
                  setCustomFactors({
                    defensiveImpact: 1.0,
                    injuryBoost: 1.0,
                    homeAwayFactor: 1.0,
                    playerInjuryFactor: 1.0,
                    trendFactor: 1.0
                  });
                  setPrediction(null);
                }}
              />
            )}

            <button
              onClick={handleSubmit}
              disabled={loading || !isFormValid()}
              className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-bold text-lg hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading
                ? 'Analyzing...'
                : compareMode
                ? 'Compare Players'
                : 'Get Prediction'}
            </button>
          </div>

          {prediction && !compareMode && (
            <>
              <PredictionVariables prediction={prediction} />
              <PredictionResults prediction={prediction} playerName={selectedPlayer} />
            </>
          )}

          {comparison && compareMode && (
            <ComparisonResults comparison={comparison} />
          )}
        </div>

        <footer className="text-center mt-12 opacity-60">
          <p>⚠️ For entertainment and statistical analysis only. Always gamble responsibly.</p>
          <p className="mt-2">Data updates every 15 minutes during game days</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

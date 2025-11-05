import React, { useState, useEffect, useCallback } from 'react';
import { fetchPlayerHistory } from '../services/api';

function HistoricalPerformance({ player, opponent }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchPlayerHistory(player, opponent);
      setHistory(data);
    } catch (err) {
      setError('Failed to fetch historical data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [player, opponent]);

  useEffect(() => {
    if (player && opponent) {
      fetchHistory();
    } else {
      setHistory(null);
    }
  }, [player, opponent, fetchHistory]);

  if (!player || !opponent) {
    return null;
  }

  if (loading) {
    return (
      <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          <span className="ml-3 text-white">Loading historical data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/20 backdrop-blur-lg rounded-xl p-6 mb-6 border border-red-500/50">
        <p className="text-red-200">{error}</p>
      </div>
    );
  }

  if (!history || history.games.length === 0) {
    return (
      <div className="bg-yellow-500/20 backdrop-blur-lg rounded-xl p-6 mb-6 border border-yellow-500/50">
        <p className="text-yellow-200">
          No historical data found for {player} vs {opponent}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6">
      <h3 className="text-xl font-bold text-white mb-4">
        📊 Historical Performance: {player} vs {opponent}
      </h3>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-500/20 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-blue-300">
            {history.total_games}
          </div>
          <div className="text-sm text-blue-200">Games Played</div>
        </div>

        <div className="bg-orange-500/20 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-orange-300">
            {history.averages.points}
          </div>
          <div className="text-sm text-orange-200">Avg Points</div>
        </div>

        <div className="bg-green-500/20 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-green-300">
            {history.averages.rebounds} / {history.averages.assists}
          </div>
          <div className="text-sm text-green-200">Avg REB / AST</div>
        </div>
      </div>

      {/* Game History Table */}
      <div className="overflow-x-auto">
        <h4 className="text-lg font-semibold text-white mb-3">Recent Games</h4>
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-white/10 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-white">Date</th>
                <th className="px-4 py-2 text-center text-white">PTS</th>
                <th className="px-4 py-2 text-center text-white">REB</th>
                <th className="px-4 py-2 text-center text-white">AST</th>
                <th className="px-4 py-2 text-center text-white">FG</th>
                <th className="px-4 py-2 text-center text-white">3PT</th>
                <th className="px-4 py-2 text-center text-white">FT</th>
                <th className="px-4 py-2 text-center text-white">+/-</th>
              </tr>
            </thead>
            <tbody>
              {history.games.map((game, index) => (
                <tr
                  key={index}
                  className="border-b border-white/10 hover:bg-white/5 transition-colors"
                >
                  <td className="px-4 py-3 text-white">
                    {new Date(game.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`font-bold ${
                      game.points >= 25 ? 'text-green-400' :
                      game.points >= 15 ? 'text-yellow-400' :
                      'text-gray-400'
                    }`}>
                      {game.points}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-blue-300">
                    {game.rebounds}
                  </td>
                  <td className="px-4 py-3 text-center text-purple-300">
                    {game.assists}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300 text-xs">
                    {game.fg_made}/{game.fg_attempted}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300 text-xs">
                    {game.three_made}/{game.three_attempted}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-300 text-xs">
                    {game.ft_made}/{game.ft_attempted}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`font-semibold ${
                      game.plus_minus > 0 ? 'text-green-400' :
                      game.plus_minus < 0 ? 'text-red-400' :
                      'text-gray-400'
                    }`}>
                      {game.plus_minus > 0 ? '+' : ''}{game.plus_minus}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Point Distribution Visualization */}
      <div className="mt-6">
        <h4 className="text-lg font-semibold text-white mb-3">Point Distribution</h4>
        <div className="flex items-end gap-2 h-24">
          {history.games.slice(0, 10).map((game, index) => {
            const maxPoints = Math.max(...history.games.map(g => g.points));
            const height = (game.points / maxPoints) * 100;

            return (
              <div
                key={index}
                className="flex-1 bg-gradient-to-t from-orange-500 to-orange-300 rounded-t-lg relative group cursor-pointer"
                style={{ height: `${height}%`, minHeight: '10%' }}
              >
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {game.points} pts
                </div>
              </div>
            );
          })}
        </div>
        <div className="text-xs text-gray-400 mt-2 text-center">
          Last {Math.min(10, history.games.length)} games (hover for details)
        </div>
      </div>
    </div>
  );
}

export default HistoricalPerformance;

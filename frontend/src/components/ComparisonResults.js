import React from 'react';

function ComparisonResults({ comparison }) {
  if (!comparison) return null;

  const { player1, player2, recommendation } = comparison;

  const getStatEntries = (predictions) => {
    return Object.entries(predictions).filter(([key]) => key !== 'analysis');
  };

  const getBetterValue = (stat, val1, val2) => {
    // Lower is better for turnovers
    if (stat === 'turnovers') {
      return val1 < val2;
    }
    // Higher is better for everything else
    return val1 > val2;
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-8 animate-fade-in">
      <h2 className="text-2xl font-bold mb-6 text-center">Player Comparison</h2>

      <div className="grid grid-cols-2 gap-8 mb-6">
        {/* Player 1 */}
        <div className="space-y-3">
          <h3 className="text-xl font-bold mb-4 text-center bg-gradient-to-r from-blue-400 to-blue-600 py-2 rounded-lg">
            {player1.name}
          </h3>
          {getStatEntries(player1.predictions).map(([stat, values]) => {
            const player2Val = player2.predictions[stat]?.prediction;
            const isBetter = getBetterValue(stat, values.prediction, player2Val);
            return (
              <div
                key={stat}
                className={`flex justify-between py-2 px-3 rounded border-b border-white/20 ${
                  isBetter ? 'bg-green-500/20' : 'bg-white/5'
                }`}
              >
                <span className="capitalize">{stat}</span>
                <span className="font-bold flex items-center">
                  {values.prediction}
                  {isBetter && <span className="ml-2 text-green-400">✓</span>}
                </span>
              </div>
            );
          })}
        </div>

        {/* Player 2 */}
        <div className="space-y-3">
          <h3 className="text-xl font-bold mb-4 text-center bg-gradient-to-r from-orange-400 to-orange-600 py-2 rounded-lg">
            {player2.name}
          </h3>
          {getStatEntries(player2.predictions).map(([stat, values]) => {
            const player1Val = player1.predictions[stat]?.prediction;
            const isBetter = getBetterValue(stat, values.prediction, player1Val);
            return (
              <div
                key={stat}
                className={`flex justify-between py-2 px-3 rounded border-b border-white/20 ${
                  isBetter ? 'bg-green-500/20' : 'bg-white/5'
                }`}
              >
                <span className="capitalize">{stat}</span>
                <span className="font-bold flex items-center">
                  {values.prediction}
                  {isBetter && <span className="ml-2 text-green-400">✓</span>}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {recommendation && (
        <div className="bg-green-500/20 border-l-4 border-green-500 p-4 rounded">
          <h3 className="font-bold mb-2 flex items-center">
            <span className="mr-2">💡</span> Recommendation
          </h3>
          <p className="text-lg">{recommendation}</p>
        </div>
      )}

      <div className="mt-6 text-center text-sm opacity-60">
        <p>Comparison based on predicted performance metrics</p>
        <p className="mt-1">Green highlights indicate better projected stats</p>
      </div>
    </div>
  );
}

export default ComparisonResults;

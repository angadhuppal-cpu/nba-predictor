import React, { useState } from 'react';

function PredictionVariables({ prediction }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!prediction) return null;

  // Extract all variables from the prediction object
  const variables = {
    // Base Historical Data
    baseData: {
      title: '📊 Historical Base Data',
      items: [
        {
          name: 'Base Average Points',
          value: prediction.base_average,
          unit: 'PPG',
          description: 'Historical average vs this opponent or season average'
        },
        {
          name: 'Games vs Opponent',
          value: prediction.factors?.games_vs_opponent || 0,
          unit: 'games',
          description: 'Number of historical matchups used in analysis'
        },
        {
          name: 'Standard Deviation',
          value: ((prediction.points.upper_bound - prediction.points.lower_bound) / 3).toFixed(1),
          unit: 'pts',
          description: 'Statistical variance in scoring performance'
        }
      ]
    },

    // Defensive Analysis
    defensiveAnalysis: {
      title: '🛡️ Defensive Matchup Analysis',
      items: [
        {
          name: 'Defensive Impact',
          value: prediction.factors?.defensive_impact || 1.0,
          unit: 'x',
          description: 'Combined effect of opponent defense rating and pace',
          isMultiplier: true
        },
        {
          name: 'Base Defensive Impact',
          value: prediction.factor_breakdown?.defensiveImpact?.base || 1.0,
          unit: 'x',
          description: 'Raw defensive impact before custom weighting',
          isMultiplier: true
        },
        {
          name: 'Defensive Weight',
          value: prediction.factor_breakdown?.defensiveImpact?.weight || 1.0,
          unit: 'x',
          description: 'Custom user adjustment for defensive impact',
          isMultiplier: true
        }
      ]
    },

    // Opponent Injury Analysis
    injuryAnalysis: {
      title: '🏥 Opponent Injury Analysis',
      items: [
        {
          name: 'Opponent Injuries Boost',
          value: prediction.factors?.opponent_injuries_boost || 1.0,
          unit: 'x',
          description: 'Scoring boost from opponent\'s injured players',
          isMultiplier: true
        },
        {
          name: 'Base Injury Boost',
          value: prediction.factor_breakdown?.injuryBoost?.base || 1.0,
          unit: 'x',
          description: 'Raw injury boost (4% per injured key player)',
          isMultiplier: true
        },
        {
          name: 'Injury Boost Weight',
          value: prediction.factor_breakdown?.injuryBoost?.weight || 1.0,
          unit: 'x',
          description: 'Custom user adjustment for injury impact',
          isMultiplier: true
        }
      ]
    },

    // Home/Away Analysis
    venueAnalysis: {
      title: '🏠 Home Court Analysis',
      items: [
        {
          name: 'Home/Away Factor',
          value: prediction.factors?.home_advantage || 1.0,
          unit: 'x',
          description: 'Home court advantage (+5%) or away penalty (-5%)',
          isMultiplier: true
        },
        {
          name: 'Base Home Factor',
          value: prediction.factor_breakdown?.homeAwayFactor?.base || 1.0,
          unit: 'x',
          description: 'Standard home/away impact',
          isMultiplier: true
        },
        {
          name: 'Home Factor Weight',
          value: prediction.factor_breakdown?.homeAwayFactor?.weight || 1.0,
          unit: 'x',
          description: 'Custom user adjustment for venue impact',
          isMultiplier: true
        }
      ]
    },

    // Player Health Analysis
    playerHealthAnalysis: {
      title: '⚕️ Player Health Analysis',
      items: [
        {
          name: 'Player Injury Impact',
          value: prediction.factors?.player_injury_impact || 1.0,
          unit: 'x',
          description: 'Performance reduction due to player injury',
          isMultiplier: true
        },
        {
          name: 'Base Player Injury',
          value: prediction.factor_breakdown?.playerInjuryFactor?.base || 1.0,
          unit: 'x',
          description: 'Injury type impact (ankle: 80%, knee: 70%, etc.)',
          isMultiplier: true
        },
        {
          name: 'Player Injury Weight',
          value: prediction.factor_breakdown?.playerInjuryFactor?.weight || 1.0,
          unit: 'x',
          description: 'Custom user adjustment for player health',
          isMultiplier: true
        }
      ]
    },

    // Trend Analysis
    trendAnalysis: {
      title: '📈 Recent Form & Trends',
      items: [
        {
          name: 'Trend Factor',
          value: prediction.factors?.trend_factor || 1.0,
          unit: 'x',
          description: 'Weight on recent vs historical performance',
          isMultiplier: true
        },
        {
          name: 'Base Trend',
          value: prediction.factor_breakdown?.trendFactor?.base || 1.0,
          unit: 'x',
          description: 'Recent 3 games vs older 3 games ratio',
          isMultiplier: true
        },
        {
          name: 'Trend Weight',
          value: prediction.factor_breakdown?.trendFactor?.weight || 1.0,
          unit: 'x',
          description: 'Custom user adjustment for trend impact',
          isMultiplier: true
        }
      ]
    },

    // Final Predictions
    finalPredictions: {
      title: '🎯 Final Predictions',
      items: [
        {
          name: 'Predicted Points',
          value: prediction.points?.prediction || 0,
          unit: 'pts',
          description: 'Final points prediction after all adjustments'
        },
        {
          name: 'Prediction Range',
          value: `${prediction.points?.lower_bound} - ${prediction.points?.upper_bound}`,
          unit: '',
          description: '68% probability range (±1.5 std dev)'
        },
        {
          name: 'Confidence Level',
          value: (prediction.points?.confidence * 100).toFixed(0),
          unit: '%',
          description: 'Statistical confidence based on data quality'
        }
      ]
    }
  };

  // Calculate total multiplier
  const totalMultiplier = (
    (prediction.factors?.defensive_impact || 1.0) *
    (prediction.factors?.opponent_injuries_boost || 1.0) *
    (prediction.factors?.home_advantage || 1.0) *
    (prediction.factors?.player_injury_impact || 1.0) *
    (prediction.factors?.trend_factor || 1.0)
  ).toFixed(3);

  const getValueColor = (item) => {
    if (!item.isMultiplier) return 'text-white';

    const value = parseFloat(item.value);
    if (value > 1.05) return 'text-green-400';
    if (value < 0.95) return 'text-red-400';
    return 'text-yellow-400';
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-white flex items-center">
          🔬 Prediction Variables
          <span className="ml-2 text-sm font-normal text-gray-300">
            (All variables evaluated in this prediction)
          </span>
        </h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-sm transition-colors"
        >
          {showDetails ? 'Hide Details' : 'Show All Variables'}
        </button>
      </div>

      {/* Summary Card */}
      <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/50 rounded-lg p-4 mb-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-gray-400 mb-1">Total Variables</div>
            <div className="text-2xl font-bold text-white">22</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Base Average</div>
            <div className="text-2xl font-bold text-blue-400">{prediction.base_average} pts</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Total Multiplier</div>
            <div className={`text-2xl font-bold ${
              totalMultiplier > 1.0 ? 'text-green-400' : totalMultiplier < 1.0 ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {totalMultiplier}x
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Final Prediction</div>
            <div className="text-2xl font-bold text-orange-400">{prediction.points?.prediction} pts</div>
          </div>
        </div>
        <div className="mt-3 text-sm text-gray-300">
          <strong>Calculation:</strong> {prediction.base_average} pts × {totalMultiplier} = {prediction.points?.prediction} pts
        </div>
      </div>

      {/* Detailed Variables */}
      {showDetails && (
        <div className="space-y-4">
          {Object.entries(variables).map(([key, section]) => (
            <div key={key} className="bg-white/5 rounded-lg p-4">
              <h4 className="font-bold text-lg text-white mb-3">{section.title}</h4>
              <div className="space-y-2">
                {section.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-start border-b border-white/10 pb-2 last:border-0">
                    <div className="flex-1">
                      <div className="font-semibold text-white">{item.name}</div>
                      <div className="text-xs text-gray-400 mt-1">{item.description}</div>
                    </div>
                    <div className="text-right ml-4">
                      <div className={`text-xl font-bold ${getValueColor(item)}`}>
                        {typeof item.value === 'number' ? item.value.toFixed(3) : item.value}
                        {item.unit && <span className="text-sm ml-1">{item.unit}</span>}
                      </div>
                      {item.isMultiplier && (
                        <div className="text-xs text-gray-400">
                          {item.value > 1.05 && `+${((item.value - 1) * 100).toFixed(1)}%`}
                          {item.value < 0.95 && `${((item.value - 1) * 100).toFixed(1)}%`}
                          {item.value >= 0.95 && item.value <= 1.05 && 'Neutral'}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Formula Breakdown */}
          <div className="bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/50 rounded-lg p-4">
            <h4 className="font-bold text-lg text-white mb-3">📐 Complete Formula</h4>
            <div className="font-mono text-sm text-gray-200 space-y-2">
              <div>
                <strong>Final Points = </strong>Base Average × Defensive Impact × Injury Boost × Home Factor × Player Injury × Trend
              </div>
              <div className="text-xs text-gray-400 mt-2">
                = {prediction.base_average} × {(prediction.factors?.defensive_impact || 1.0).toFixed(3)} × {(prediction.factors?.opponent_injuries_boost || 1.0).toFixed(3)} × {(prediction.factors?.home_advantage || 1.0).toFixed(3)} × {(prediction.factors?.player_injury_impact || 1.0).toFixed(3)} × {(prediction.factors?.trend_factor || 1.0).toFixed(3)}
              </div>
              <div className="text-xs text-gray-400">
                = <strong className="text-orange-400 text-lg">{prediction.points?.prediction} points</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats when collapsed */}
      {!showDetails && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Defensive Impact</div>
            <div className={`text-lg font-bold ${
              (prediction.factors?.defensive_impact || 1.0) > 1.05 ? 'text-green-400' :
              (prediction.factors?.defensive_impact || 1.0) < 0.95 ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {(prediction.factors?.defensive_impact || 1.0).toFixed(3)}x
            </div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Opponent Injuries</div>
            <div className={`text-lg font-bold ${
              (prediction.factors?.opponent_injuries_boost || 1.0) > 1.05 ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {(prediction.factors?.opponent_injuries_boost || 1.0).toFixed(3)}x
            </div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Home Advantage</div>
            <div className={`text-lg font-bold ${
              (prediction.factors?.home_advantage || 1.0) > 1.0 ? 'text-green-400' :
              (prediction.factors?.home_advantage || 1.0) < 1.0 ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {(prediction.factors?.home_advantage || 1.0).toFixed(3)}x
            </div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Player Health</div>
            <div className={`text-lg font-bold ${
              (prediction.factors?.player_injury_impact || 1.0) < 1.0 ? 'text-red-400' : 'text-green-400'
            }`}>
              {(prediction.factors?.player_injury_impact || 1.0).toFixed(3)}x
            </div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Recent Trend</div>
            <div className={`text-lg font-bold ${
              (prediction.factors?.trend_factor || 1.0) > 1.05 ? 'text-green-400' :
              (prediction.factors?.trend_factor || 1.0) < 0.95 ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {(prediction.factors?.trend_factor || 1.0).toFixed(3)}x
            </div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Matchup Games</div>
            <div className="text-lg font-bold text-blue-400">
              {prediction.factors?.games_vs_opponent || 0}
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-4 bg-purple-500/20 border border-purple-500/50 rounded-lg p-3">
        <p className="text-sm text-purple-200">
          <strong>💡 Understanding the variables:</strong> Each prediction uses 22+ variables including historical data,
          defensive matchups, injuries, venue, player health, and recent trends. Values above 1.0x increase the prediction,
          while values below 1.0x decrease it. Click "Show All Variables" to see the complete breakdown.
        </p>
      </div>
    </div>
  );
}

export default PredictionVariables;

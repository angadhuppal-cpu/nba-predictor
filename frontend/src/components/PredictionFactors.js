import React, { useState } from 'react';

function PredictionFactors({ factors, setFactors, onReset }) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const defaultFactors = {
    defensiveImpact: 1.0,
    injuryBoost: 1.0,
    homeAwayFactor: 1.0,
    playerInjuryFactor: 1.0,
    trendFactor: 1.0
  };

  const handleFactorChange = (factorName, value) => {
    setFactors({
      ...factors,
      [factorName]: parseFloat(value)
    });
  };

  const handleReset = () => {
    setFactors(defaultFactors);
    if (onReset) onReset();
  };

  const factorDescriptions = {
    defensiveImpact: {
      name: 'Defensive Matchup Impact',
      description: 'How opponent\'s defensive rating affects scoring',
      range: '0.5 - 1.5',
      default: 1.0,
      explanation: 'Higher = More emphasis on opponent defense strength'
    },
    injuryBoost: {
      name: 'Opponent Injury Boost',
      description: 'Scoring boost when opponent has key players out',
      range: '0.0 - 2.0',
      default: 1.0,
      explanation: 'Higher = More boost from opponent injuries'
    },
    homeAwayFactor: {
      name: 'Home Court Advantage',
      description: 'Impact of playing home vs away',
      range: '0.5 - 1.5',
      default: 1.0,
      explanation: 'Higher = Stronger home court advantage effect'
    },
    playerInjuryFactor: {
      name: 'Player Health Impact',
      description: 'How player\'s injury status affects performance',
      range: '0.0 - 1.5',
      default: 1.0,
      explanation: 'Higher = More severe impact from injuries'
    },
    trendFactor: {
      name: 'Recent Form/Trend',
      description: 'Weight given to recent performance trends',
      range: '0.5 - 1.5',
      default: 1.0,
      explanation: 'Higher = More weight on recent vs historical form'
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-white flex items-center">
          ⚙️ Prediction Factors
          <span className="ml-2 text-sm font-normal text-gray-300">
            (Customize how predictions are calculated)
          </span>
        </h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm transition-colors"
        >
          {showAdvanced ? 'Hide Controls' : 'Show Controls'}
        </button>
      </div>

      {/* Factor Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        {Object.entries(factorDescriptions).map(([key, info]) => {
          const value = factors[key];
          const isModified = value !== info.default;

          return (
            <div
              key={key}
              className={`bg-white/5 rounded-lg p-3 border ${
                isModified ? 'border-orange-500' : 'border-white/20'
              }`}
            >
              <div className="text-xs text-gray-400 mb-1">{info.name}</div>
              <div className={`text-2xl font-bold ${
                isModified ? 'text-orange-400' : 'text-white'
              }`}>
                {value.toFixed(2)}x
              </div>
              {isModified && (
                <div className="text-xs text-orange-300 mt-1">
                  Modified
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Advanced Controls */}
      {showAdvanced && (
        <div className="space-y-4 bg-white/5 rounded-lg p-4">
          {Object.entries(factorDescriptions).map(([key, info]) => (
            <div key={key} className="border-b border-white/10 pb-4 last:border-0">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <label className="font-semibold text-white">{info.name}</label>
                  <p className="text-sm text-gray-400">{info.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    💡 {info.explanation}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-orange-400">
                    {factors[key].toFixed(2)}x
                  </div>
                  <div className="text-xs text-gray-400">
                    Range: {info.range}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={info.range.split(' - ')[0]}
                  max={info.range.split(' - ')[1]}
                  step="0.1"
                  value={factors[key]}
                  onChange={(e) => handleFactorChange(key, e.target.value)}
                  className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <input
                  type="number"
                  min={info.range.split(' - ')[0]}
                  max={info.range.split(' - ')[1]}
                  step="0.1"
                  value={factors[key]}
                  onChange={(e) => handleFactorChange(key, e.target.value)}
                  className="w-20 px-3 py-1 bg-gray-700 text-white rounded-lg text-center"
                />
              </div>
            </div>
          ))}

          <div className="flex gap-4 pt-4">
            <button
              onClick={handleReset}
              className="flex-1 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg font-semibold transition-colors"
            >
              🔄 Reset to Defaults
            </button>
            <button
              onClick={() => setShowAdvanced(false)}
              className="flex-1 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-semibold transition-colors"
            >
              ✓ Apply Changes
            </button>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-4 bg-blue-500/20 border border-blue-500/50 rounded-lg p-3">
        <p className="text-sm text-blue-200">
          <strong>💡 How it works:</strong> These factors control how much weight is given to different
          aspects of the prediction. Higher values = stronger impact. Adjust based on your own analysis
          and basketball knowledge!
        </p>
      </div>
    </div>
  );
}

export default PredictionFactors;

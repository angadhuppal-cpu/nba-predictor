import React from 'react';

function PredictionResults({ prediction, playerName }) {
  if (!prediction) return null;

  const stats = Object.entries(prediction).filter(([key]) => key !== 'analysis');

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-8 animate-fade-in">
      <h2 className="text-2xl font-bold mb-6">Prediction Results for {playerName}</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map(([stat, values]) => (
          <div key={stat} className="bg-white/20 rounded-lg p-4 hover:bg-white/30 transition-colors">
            <div className="text-sm uppercase opacity-80 mb-1">{stat}</div>
            <div className="text-3xl font-bold mb-1">{values.prediction}</div>
            <div className="text-xs opacity-60 mb-2">
              {values.lower_bound} - {values.upper_bound}
            </div>
            <div className="relative w-full bg-gray-700 rounded-full h-2">
              <div
                className="absolute h-2 bg-gradient-to-r from-green-500 to-blue-500 rounded-full"
                style={{ width: `${values.confidence * 100}%` }}
              ></div>
            </div>
            <div className="text-xs mt-1">
              Confidence: {(values.confidence * 100).toFixed(0)}%
            </div>
          </div>
        ))}
      </div>

      {prediction.analysis && (
        <div className="bg-yellow-500/20 border-l-4 border-yellow-500 p-4 rounded">
          <h3 className="font-bold mb-2 flex items-center">
            <span className="mr-2">📊</span> Analysis
          </h3>
          <p className="whitespace-pre-line text-sm leading-relaxed">
            {prediction.analysis}
          </p>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-center text-sm opacity-80">
        <div className="bg-white/10 rounded-lg p-3">
          <div className="font-semibold">Model Type</div>
          <div>Ensemble ML</div>
        </div>
        <div className="bg-white/10 rounded-lg p-3">
          <div className="font-semibold">Factors Analyzed</div>
          <div>15+ Variables</div>
        </div>
        <div className="bg-white/10 rounded-lg p-3">
          <div className="font-semibold">Prediction Time</div>
          <div>Real-time</div>
        </div>
      </div>
    </div>
  );
}

export default PredictionResults;

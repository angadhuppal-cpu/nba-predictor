import React, { useState } from 'react';
import { evaluateParlay } from '../services/api';
import useSavedBets from '../hooks/useSavedBets';

const STAT_OPTIONS = [
  { value: 'points', label: 'Points' },
  { value: 'rebounds', label: 'Rebounds' },
  { value: 'assists', label: 'Assists' },
  { value: 'threes', label: '3PT Made' },
  { value: 'steals', label: 'Steals' },
  { value: 'blocks', label: 'Blocks' },
  { value: 'pra', label: 'P+R+A' },
  { value: 'pr', label: 'P+R' },
  { value: 'pa', label: 'P+A' },
  { value: 'ra', label: 'R+A' },
];

const emptyLeg = () => ({
  player: '',
  stat: 'points',
  line: '',
  direction: 'over',
  opponent: '',
});

export default function ParlayBuilder() {
  const [legs, setLegs] = useState([emptyLeg(), emptyLeg()]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addBet } = useSavedBets();

  const updateLeg = (index, patch) => {
    setLegs((prev) => prev.map((leg, i) => (i === index ? { ...leg, ...patch } : leg)));
  };

  const addLeg = () => {
    if (legs.length >= 6) return;
    setLegs((prev) => [...prev, emptyLeg()]);
  };

  const removeLeg = (index) => {
    if (legs.length <= 1) return;
    setLegs((prev) => prev.filter((_, i) => i !== index));
  };

  const isValid = legs.every((l) => l.player.trim() && l.line !== '' && !isNaN(parseFloat(l.line)));

  const handleEvaluate = async () => {
    if (!isValid) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await evaluateParlay(
        legs.map((l) => ({
          player: l.player.trim(),
          stat: l.stat,
          line: parseFloat(l.line),
          direction: l.direction,
          opponent: l.opponent.trim() || undefined,
        }))
      );
      setResult(res);
    } catch (err) {
      setError(err.message || 'Failed to evaluate parlay.');
    } finally {
      setLoading(false);
    }
  };

  const saveParlay = () => {
    if (!result || result.combined_probability == null) return;
    addBet({
      type: 'parlay',
      legs: legs.map((l) => ({
        player: l.player,
        stat: l.stat,
        line: parseFloat(l.line),
        direction: l.direction,
        opponent: l.opponent || null,
      })),
      combined_probability: result.combined_probability,
      fair_american_odds: result.fair_american_odds,
      recommendation: result.recommendation,
    });
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6">
      <h2 className="text-2xl font-bold mb-1">🎯 Parlay Builder</h2>
      <p className="text-sm opacity-70 mb-6">
        Combine 2–6 prop legs. We multiply individual hit probabilities and
        apply a small same-game correlation discount.
      </p>

      <div className="space-y-3">
        {legs.map((leg, i) => (
          <div
            key={i}
            className="bg-white/5 border border-white/10 rounded-lg p-3 grid grid-cols-1 md:grid-cols-12 gap-2 items-center"
          >
            <div className="md:col-span-1 text-sm font-bold opacity-70">#{i + 1}</div>
            <input
              value={leg.player}
              onChange={(e) => updateLeg(i, { player: e.target.value })}
              placeholder="Player"
              className="md:col-span-3 px-2 py-1.5 rounded bg-white/10 border border-white/20"
            />
            <select
              value={leg.stat}
              onChange={(e) => updateLeg(i, { stat: e.target.value })}
              className="md:col-span-2 px-2 py-1.5 rounded bg-white/10 border border-white/20"
            >
              {STAT_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
            <select
              value={leg.direction}
              onChange={(e) => updateLeg(i, { direction: e.target.value })}
              className="md:col-span-1 px-2 py-1.5 rounded bg-white/10 border border-white/20"
            >
              <option value="over">O</option>
              <option value="under">U</option>
            </select>
            <input
              value={leg.line}
              onChange={(e) => updateLeg(i, { line: e.target.value })}
              type="number"
              step="0.5"
              placeholder="Line"
              className="md:col-span-2 px-2 py-1.5 rounded bg-white/10 border border-white/20"
            />
            <input
              value={leg.opponent}
              onChange={(e) => updateLeg(i, { opponent: e.target.value.toUpperCase() })}
              placeholder="vs (BOS)"
              className="md:col-span-2 px-2 py-1.5 rounded bg-white/10 border border-white/20"
            />
            <button
              onClick={() => removeLeg(i)}
              disabled={legs.length === 1}
              className="md:col-span-1 px-2 py-1.5 bg-red-500/40 hover:bg-red-500/60 disabled:opacity-30 rounded"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2 mt-4">
        <button
          onClick={addLeg}
          disabled={legs.length >= 6}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded disabled:opacity-30"
        >
          + Add leg
        </button>
        <button
          onClick={handleEvaluate}
          disabled={!isValid || loading}
          className="px-4 py-2 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 rounded font-bold"
        >
          {loading ? 'Calculating…' : 'Evaluate Parlay'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-500/20 border border-red-500 text-red-200 rounded">
          {error}
        </div>
      )}

      {result && result.combined_probability != null && (
        <div className="mt-6 bg-black/30 rounded-lg p-5">
          <div className="flex flex-wrap items-baseline gap-4 mb-4">
            <div>
              <div className="text-sm opacity-70">Combined hit probability</div>
              <div className="text-4xl font-bold">
                {(result.combined_probability * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-sm opacity-70">Fair odds</div>
              <div className="text-2xl font-bold">
                {result.fair_american_odds > 0
                  ? `+${result.fair_american_odds}`
                  : result.fair_american_odds}
              </div>
            </div>
            <div>
              <div className="text-sm opacity-70">Verdict</div>
              <div
                className={`text-2xl font-bold ${
                  result.recommendation === 'STRONG'
                    ? 'text-green-400'
                    : result.recommendation === 'PLAYABLE'
                    ? 'text-yellow-300'
                    : result.recommendation === 'DART'
                    ? 'text-orange-400'
                    : 'text-red-400'
                }`}
              >
                {result.recommendation}
              </div>
            </div>
            <button
              onClick={saveParlay}
              className="ml-auto px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded text-sm"
            >
              💾 Save to history
            </button>
          </div>

          {result.same_game_legs > 0 && (
            <p className="text-xs opacity-70 mb-3">
              ⚠ {result.same_game_legs} same-game correlation discount applied.
            </p>
          )}

          <div className="space-y-2">
            <h4 className="text-sm font-bold opacity-70 uppercase tracking-wide">
              Per-leg breakdown
            </h4>
            {result.legs.map((leg, i) => (
              <div key={i} className="text-sm bg-white/5 rounded p-2">
                {leg.error ? (
                  <span className="text-red-300">
                    Leg {i + 1}: {leg.error}
                  </span>
                ) : (
                  <>
                    <strong>{leg.player}</strong> {leg.direction} {leg.line}{' '}
                    {leg.stat_label} →{' '}
                    <span className="font-mono">
                      {leg.blended_probability != null
                        ? `${(leg.blended_probability * 100).toFixed(1)}%`
                        : 'n/a'}
                    </span>{' '}
                    <span className="opacity-70">({leg.recommendation})</span>
                  </>
                )}
              </div>
            ))}
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <ul className="mt-3 text-xs text-yellow-300">
              {result.warnings.map((w, i) => (
                <li key={i}>⚠ {w}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

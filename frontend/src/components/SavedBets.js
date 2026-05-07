import React, { useMemo } from 'react';
import useSavedBets from '../hooks/useSavedBets';

const RESULT_OPTIONS = [
  { value: null, label: 'Pending' },
  { value: 'win', label: 'Win' },
  { value: 'loss', label: 'Loss' },
  { value: 'push', label: 'Push' },
];

function summarize(bet) {
  if (bet.type === 'parlay') {
    return `${bet.legs?.length || 0}-leg parlay`;
  }
  return `${bet.player} ${bet.direction?.toUpperCase()} ${bet.line} ${bet.stat}`;
}

export default function SavedBets() {
  const { bets, removeBet, updateBet, clearAll } = useSavedBets();

  const stats = useMemo(() => {
    const wins = bets.filter((b) => b.result === 'win').length;
    const losses = bets.filter((b) => b.result === 'loss').length;
    const pushes = bets.filter((b) => b.result === 'push').length;
    const pending = bets.filter((b) => !b.result).length;
    const total = wins + losses;
    const winPct = total > 0 ? wins / total : null;
    return { wins, losses, pushes, pending, winPct };
  }, [bets]);

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 className="text-2xl font-bold">📒 Bet History</h2>
        {bets.length > 0 && (
          <button
            onClick={() => {
              if (window.confirm('Clear all saved bets? This cannot be undone.')) {
                clearAll();
              }
            }}
            className="px-3 py-1.5 bg-red-500/40 hover:bg-red-500/60 rounded text-sm"
          >
            Clear all
          </button>
        )}
      </div>

      {bets.length === 0 ? (
        <p className="opacity-70">
          No saved bets yet. Use the 💾 button on the Slate or Parlay tabs to
          track plays here. Stored locally in your browser only.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4 text-sm">
            <Stat label="Total" value={bets.length} />
            <Stat label="Wins" value={stats.wins} color="text-green-400" />
            <Stat label="Losses" value={stats.losses} color="text-red-400" />
            <Stat label="Pending" value={stats.pending} />
            <Stat
              label="Win %"
              value={
                stats.winPct != null ? `${(stats.winPct * 100).toFixed(0)}%` : '—'
              }
              color="text-yellow-300"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left opacity-70 border-b border-white/10">
                  <th className="py-2 pr-2">Date</th>
                  <th className="py-2 pr-2">Bet</th>
                  <th className="py-2 pr-2">Probability</th>
                  <th className="py-2 pr-2">Result</th>
                  <th className="py-2 pr-2"></th>
                </tr>
              </thead>
              <tbody>
                {bets.map((bet) => (
                  <tr key={bet.id} className="border-b border-white/5">
                    <td className="py-2 pr-2 text-xs opacity-70">
                      {new Date(bet.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2 pr-2">
                      {summarize(bet)}
                      {bet.opponent && (
                        <span className="opacity-60"> vs {bet.opponent}</span>
                      )}
                      {bet.type === 'parlay' && bet.legs && (
                        <details className="text-xs opacity-70">
                          <summary className="cursor-pointer">
                            view {bet.legs.length} legs
                          </summary>
                          {bet.legs.map((l, i) => (
                            <div key={i}>
                              {l.player} {l.direction} {l.line} {l.stat}
                            </div>
                          ))}
                        </details>
                      )}
                    </td>
                    <td className="py-2 pr-2 font-mono">
                      {bet.combined_probability != null
                        ? `${(bet.combined_probability * 100).toFixed(1)}%`
                        : bet.probability != null
                        ? `${(bet.probability * 100).toFixed(1)}%`
                        : '—'}
                    </td>
                    <td className="py-2 pr-2">
                      <select
                        value={bet.result ?? ''}
                        onChange={(e) =>
                          updateBet(bet.id, {
                            result: e.target.value === '' ? null : e.target.value,
                          })
                        }
                        className="px-2 py-1 rounded bg-white/10 border border-white/20"
                      >
                        {RESULT_OPTIONS.map((r) => (
                          <option key={r.label} value={r.value ?? ''}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 pr-2">
                      <button
                        onClick={() => removeBet(bet.id)}
                        className="px-2 py-1 bg-red-500/40 hover:bg-red-500/60 rounded text-xs"
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, color = '' }) {
  return (
    <div className="bg-white/5 rounded p-3 text-center">
      <div className="text-xs opacity-70 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

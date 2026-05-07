import React, { useEffect, useState } from 'react';
import { fetchTodaysSlate } from '../services/api';
import useSavedBets from '../hooks/useSavedBets';

function todayString() {
  return new Date().toISOString().split('T')[0];
}

export default function TodaysSlate() {
  const [date, setDate] = useState(todayString());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addBet } = useSavedBets();

  const loadSlate = async (d) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTodaysSlate(d);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load slate.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSlate(date);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  return (
    <div className="space-y-6">
      <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl font-bold">📅 Today's Slate</h2>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="px-3 py-1.5 rounded bg-white/10 border border-white/20"
            />
            <button
              onClick={() => loadSlate(date)}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded text-sm"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {loading && <p className="opacity-70">Scanning slate…</p>}
        {error && (
          <div className="p-3 bg-red-500/20 border border-red-500 text-red-200 rounded">
            {error}
          </div>
        )}

        {data && data.games && data.games.length === 0 && (
          <p className="opacity-70">
            {data.message ||
              'No games scheduled in the local DB for this date. Try refreshing your data pipeline (python fetch_game_logs.py / nba_data_pipeline.py).'}
          </p>
        )}

        {data && data.games && data.games.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.games.map((g) => (
              <div
                key={g.game_id}
                className="bg-white/5 border border-white/10 rounded p-3"
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold">
                    {g.away_team} @ {g.home_team}
                  </span>
                  <span className="text-xs opacity-70">{g.time}</span>
                </div>
                <div className="text-xs opacity-70 grid grid-cols-2 gap-2">
                  <div>
                    <div className="font-bold">{g.away_team} top scorers</div>
                    {(g.away_top_scorers || []).map((p) => (
                      <div key={p.name}>
                        {p.name} <span className="opacity-60">({p.ppg?.toFixed(1)} ppg)</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="font-bold">{g.home_team} top scorers</div>
                    {(g.home_top_scorers || []).map((p) => (
                      <div key={p.name}>
                        {p.name} <span className="opacity-60">({p.ppg?.toFixed(1)} ppg)</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {data && data.edges && data.edges.length > 0 && (
        <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6">
          <h3 className="text-xl font-bold mb-3">🔥 Top Edges Tonight</h3>
          <p className="text-sm opacity-70 mb-4">
            Sorted by largest statistical edge vs the line.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left opacity-70 border-b border-white/10">
                  <th className="py-2 pr-2">Player</th>
                  <th className="py-2 pr-2">Bet</th>
                  <th className="py-2 pr-2">Probability</th>
                  <th className="py-2 pr-2">Edge</th>
                  <th className="py-2 pr-2">Verdict</th>
                  <th className="py-2 pr-2">Save</th>
                </tr>
              </thead>
              <tbody>
                {data.edges.map((e, i) => (
                  <tr key={i} className="border-b border-white/5">
                    <td className="py-2 pr-2">
                      {e.player}
                      <div className="text-xs opacity-60">
                        {e.team} vs {e.opponent}
                      </div>
                    </td>
                    <td className="py-2 pr-2">
                      <span className="uppercase font-bold">{e.direction}</span>{' '}
                      {e.line} {e.stat}
                    </td>
                    <td className="py-2 pr-2 font-mono">
                      {(e.probability * 100).toFixed(1)}%
                    </td>
                    <td
                      className={`py-2 pr-2 font-mono ${
                        e.edge > 0 ? 'text-green-300' : 'text-red-300'
                      }`}
                    >
                      {e.edge > 0 ? '+' : ''}
                      {(e.edge * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-2">
                      <span
                        className={
                          e.recommendation?.includes('STRONG')
                            ? 'text-green-400'
                            : e.recommendation?.includes('LEAN')
                            ? 'text-yellow-300'
                            : 'opacity-70'
                        }
                      >
                        {e.recommendation}
                      </span>
                    </td>
                    <td className="py-2 pr-2">
                      <button
                        onClick={() =>
                          addBet({
                            type: 'single',
                            player: e.player,
                            opponent: e.opponent,
                            stat: e.stat,
                            line: e.line,
                            direction: e.direction,
                            probability: e.probability,
                            edge: e.edge,
                            recommendation: e.recommendation,
                          })
                        }
                        className="px-2 py-1 bg-blue-500/60 hover:bg-blue-500 rounded text-xs"
                      >
                        💾
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

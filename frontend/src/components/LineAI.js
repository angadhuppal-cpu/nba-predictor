import React, { useState, useRef, useEffect } from 'react';
import { chatWithAdvisor, resetAdvisor, evaluateLine } from '../services/api';

const SAMPLE_PROMPTS = [
  "Will LeBron go OVER 24.5 points tonight vs BOS?",
  "Find the best prop lines for Jayson Tatum vs the Knicks tonight.",
  "Is Luka Doncic's 9.5 assists line a hit vs MEM?",
  "Should I take Joel Embiid OVER 10.5 rebounds vs MIA?",
];

function MessageBubble({ role, text }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 whitespace-pre-wrap ${
          isUser
            ? 'bg-orange-500 text-white'
            : 'bg-white/10 text-white border border-white/20'
        }`}
      >
        {text}
      </div>
    </div>
  );
}

function ToolCallTrace({ calls }) {
  if (!calls || calls.length === 0) return null;
  return (
    <details className="mt-2 text-xs opacity-70">
      <summary className="cursor-pointer">
        {calls.length} tool call{calls.length === 1 ? '' : 's'}: {calls.map(c => c.name).join(', ')}
      </summary>
      <pre className="mt-2 p-2 bg-black/30 rounded overflow-x-auto max-h-60">
        {JSON.stringify(calls, null, 2)}
      </pre>
    </details>
  );
}

export default function LineAI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId] = useState(() => `session-${Date.now()}`);

  // Quick-eval form
  const [qPlayer, setQPlayer] = useState('');
  const [qStat, setQStat] = useState('points');
  const [qLine, setQLine] = useState('');
  const [qDirection, setQDirection] = useState('over');
  const [qOpponent, setQOpponent] = useState('');
  const [qResult, setQResult] = useState(null);
  const [qLoading, setQLoading] = useState(false);

  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || sending) return;
    setError(null);
    setSending(true);
    setMessages((m) => [...m, { role: 'user', text: message }]);
    setInput('');
    try {
      const res = await chatWithAdvisor(message, sessionId);
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: res.reply, tool_calls: res.tool_calls },
      ]);
    } catch (err) {
      setError(err.message || 'Failed to reach AI advisor.');
    } finally {
      setSending(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetAdvisor(sessionId);
      setMessages([]);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleQuickEval = async (e) => {
    e.preventDefault();
    if (!qPlayer || !qLine) return;
    setQLoading(true);
    setQResult(null);
    try {
      const res = await evaluateLine({
        player: qPlayer,
        stat: qStat,
        line: parseFloat(qLine),
        direction: qDirection,
        opponent: qOpponent || undefined,
      });
      setQResult(res);
    } catch (err) {
      setQResult({ error: err.message });
    } finally {
      setQLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Chat panel */}
      <div className="lg:col-span-2 bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6 flex flex-col h-[700px]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">🤖 NBA Line Advisor</h2>
          <button
            onClick={handleReset}
            className="text-sm px-3 py-1 rounded bg-gray-700 hover:bg-gray-600"
          >
            Reset chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto pr-2">
          {messages.length === 0 && (
            <div className="text-center opacity-70 py-8">
              <p className="mb-4">
                Ask about any sportsbook prop line. The AI uses your local
                game-log database, normal-distribution math, and NBA context to
                give a hit/miss recommendation with confidence.
              </p>
              <div className="grid gap-2">
                {SAMPLE_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    className="text-left text-sm px-3 py-2 rounded bg-white/5 hover:bg-white/10 border border-white/10"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i}>
              <MessageBubble role={m.role} text={m.text} />
              {m.role === 'assistant' && <ToolCallTrace calls={m.tool_calls} />}
            </div>
          ))}
          {sending && (
            <div className="text-sm opacity-70 italic">AI is reasoning…</div>
          )}
          <div ref={endRef} />
        </div>

        {error && (
          <div className="mt-3 p-2 bg-red-500/20 border border-red-500 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="mt-4 flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Will [player] go OVER/UNDER [line] [stat] vs [team]?"
            className="flex-1 px-4 py-2 rounded-lg bg-white/10 border border-white/20 placeholder-white/40 focus:outline-none focus:border-orange-400"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="px-4 py-2 bg-orange-500 rounded-lg hover:bg-orange-600 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>

      {/* Quick-eval panel */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl shadow-2xl p-6">
        <h3 className="text-xl font-bold mb-3">⚡ Quick line check</h3>
        <p className="text-xs opacity-70 mb-4">
          Pure-math evaluation — no LLM call. Useful for fast comparisons.
        </p>
        <form onSubmit={handleQuickEval} className="space-y-3">
          <input
            value={qPlayer}
            onChange={(e) => setQPlayer(e.target.value)}
            placeholder="Player full name"
            className="w-full px-3 py-2 rounded bg-white/10 border border-white/20 placeholder-white/40"
          />
          <div className="grid grid-cols-2 gap-2">
            <select
              value={qStat}
              onChange={(e) => setQStat(e.target.value)}
              className="px-3 py-2 rounded bg-white/10 border border-white/20"
            >
              <option value="points">Points</option>
              <option value="rebounds">Rebounds</option>
              <option value="assists">Assists</option>
              <option value="threes">3PT Made</option>
              <option value="steals">Steals</option>
              <option value="blocks">Blocks</option>
              <option value="pra">P+R+A</option>
              <option value="pr">P+R</option>
              <option value="pa">P+A</option>
              <option value="ra">R+A</option>
            </select>
            <select
              value={qDirection}
              onChange={(e) => setQDirection(e.target.value)}
              className="px-3 py-2 rounded bg-white/10 border border-white/20"
            >
              <option value="over">Over</option>
              <option value="under">Under</option>
            </select>
          </div>
          <input
            value={qLine}
            onChange={(e) => setQLine(e.target.value)}
            type="number"
            step="0.5"
            placeholder="Line (e.g. 24.5)"
            className="w-full px-3 py-2 rounded bg-white/10 border border-white/20 placeholder-white/40"
          />
          <input
            value={qOpponent}
            onChange={(e) => setQOpponent(e.target.value.toUpperCase())}
            placeholder="Opponent abbr (BOS, optional)"
            className="w-full px-3 py-2 rounded bg-white/10 border border-white/20 placeholder-white/40"
          />
          <button
            type="submit"
            disabled={qLoading || !qPlayer || !qLine}
            className="w-full py-2 bg-blue-500 rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {qLoading ? 'Crunching…' : 'Evaluate'}
          </button>
        </form>

        {qResult && (
          <div className="mt-4 text-sm">
            {qResult.error ? (
              <p className="text-red-300">{qResult.error}</p>
            ) : (
              <div className="space-y-1">
                <p className="text-lg font-bold">
                  {qResult.recommendation}
                  <span className="ml-2 text-xs opacity-70">
                    ({qResult.confidence})
                  </span>
                </p>
                {qResult.blended_probability != null && (
                  <p>
                    Blended {qResult.direction} probability:{' '}
                    <strong>{(qResult.blended_probability * 100).toFixed(1)}%</strong>
                  </p>
                )}
                {qResult.projection != null && (
                  <p>Projection: {qResult.projection}</p>
                )}
                {qResult.recent_avg != null && (
                  <p>Last-10 avg: {qResult.recent_avg}</p>
                )}
                {qResult.season_avg != null && (
                  <p>Season avg: {qResult.season_avg}</p>
                )}
                {qResult.vs_opponent_avg != null && (
                  <p>vs opponent avg: {qResult.vs_opponent_avg}</p>
                )}
                {qResult.hit_rate_recent != null && (
                  <p>
                    Hit rate last 10: {(qResult.hit_rate_recent * 100).toFixed(0)}%
                  </p>
                )}
                {qResult.warnings && qResult.warnings.length > 0 && (
                  <ul className="text-xs text-yellow-300 mt-2">
                    {qResult.warnings.map((w, i) => (
                      <li key={i}>⚠ {w}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

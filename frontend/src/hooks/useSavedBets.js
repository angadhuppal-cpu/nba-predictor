import { useEffect, useState, useCallback } from 'react';

const STORAGE_KEY = 'nba-line-ai.saved-bets';

function readBets() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

function writeBets(bets) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bets));
  } catch (_) {
    /* quota exceeded — silently drop */
  }
}

export default function useSavedBets() {
  const [bets, setBets] = useState(() => readBets());

  useEffect(() => {
    writeBets(bets);
  }, [bets]);

  const addBet = useCallback((bet) => {
    const entry = {
      id: `bet-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      created_at: new Date().toISOString(),
      result: null, // 'win' | 'loss' | 'push' | null (pending)
      ...bet,
    };
    setBets((prev) => [entry, ...prev]);
    return entry;
  }, []);

  const removeBet = useCallback((id) => {
    setBets((prev) => prev.filter((b) => b.id !== id));
  }, []);

  const updateBet = useCallback((id, patch) => {
    setBets((prev) => prev.map((b) => (b.id === id ? { ...b, ...patch } : b)));
  }, []);

  const clearAll = useCallback(() => setBets([]), []);

  return { bets, addBet, removeBet, updateBet, clearAll };
}

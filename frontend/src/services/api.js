/**
 * API Service for NBA Prediction System
 * Handles all backend API communications
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * Fetch list of available players
 */
export async function fetchPlayers() {
  return fetchAPI('/players');
}

/**
 * Fetch list of NBA teams
 */
export async function fetchTeams() {
  return fetchAPI('/teams');
}

/**
 * Predict player performance
 */
export async function predictPerformance(data) {
  return fetchAPI('/predict', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Compare two players' predicted performance
 */
export async function comparePlayers(data) {
  return fetchAPI('/compare', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get schedule for a specific date
 */
export async function fetchSchedule(date) {
  return fetchAPI(`/schedule/${date}`);
}

/**
 * Get current injury report
 */
export async function fetchInjuries() {
  return fetchAPI('/injuries');
}

/**
 * Get player's recent performance
 */
export async function fetchPlayerRecent(playerId, games = 10) {
  return fetchAPI(`/player/${playerId}/recent?games=${games}`);
}

/**
 * Get player's matchup history against a team
 */
export async function fetchMatchupHistory(playerId, team, limit = 10) {
  return fetchAPI(`/player/${playerId}/matchup/${team}?limit=${limit}`);
}

/**
 * Get player's historical performance vs opponent
 */
export async function fetchPlayerHistory(playerName, opponent) {
  return fetchAPI(`/history?player=${encodeURIComponent(playerName)}&opponent=${encodeURIComponent(opponent)}`);
}

/**
 * Trigger data update
 */
export async function updateData() {
  return fetchAPI('/update-data', {
    method: 'POST',
  });
}

/**
 * Get system statistics
 */
export async function fetchStats() {
  return fetchAPI('/stats');
}

/**
 * Health check
 */
export async function healthCheck() {
  return fetchAPI('/health');
}

/**
 * Evaluate a sportsbook prop line (pure stats, no LLM).
 */
export async function evaluateLine(payload) {
  return fetchAPI('/line/evaluate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Find the strongest-edge prop lines for a player.
 */
export async function findBestLines(payload) {
  return fetchAPI('/line/best', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Send a message to the AI advisor (Claude with tool-use).
 */
export async function chatWithAdvisor(message, sessionId = 'default') {
  return fetchAPI('/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}

/**
 * Reset an AI advisor conversation session.
 */
export async function resetAdvisor(sessionId = 'default') {
  return fetchAPI('/ai/reset', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/**
 * Evaluate a parlay (multiple legs combined).
 */
export async function evaluateParlay(legs) {
  return fetchAPI('/parlay/evaluate', {
    method: 'POST',
    body: JSON.stringify({ legs }),
  });
}

/**
 * Fetch today's slate: tonight's games and league-wide best edges.
 */
export async function fetchTodaysSlate(date) {
  const qs = date ? `?date=${date}` : '';
  return fetchAPI(`/slate/today${qs}`);
}

/**
 * Fetch tonight's games only.
 */
export async function fetchTodaysGames(date) {
  const qs = date ? `?date=${date}` : '';
  return fetchAPI(`/games/today${qs}`);
}

const api = {
  fetchPlayers,
  fetchTeams,
  predictPerformance,
  comparePlayers,
  fetchSchedule,
  fetchInjuries,
  fetchPlayerRecent,
  fetchMatchupHistory,
  updateData,
  fetchStats,
  healthCheck,
  evaluateLine,
  findBestLines,
  chatWithAdvisor,
  resetAdvisor,
  evaluateParlay,
  fetchTodaysSlate,
  fetchTodaysGames,
};

export default api;

import React from 'react';

function PredictionForm({
  selectedPlayer,
  setSelectedPlayer,
  opponent,
  setOpponent,
  gameDate,
  setGameDate,
  isHome,
  setIsHome,
  injuryStatus,
  setInjuryStatus,
  player2,
  setPlayer2,
  players,
  teams,
  compareMode
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <div>
        <label className="block text-sm font-medium mb-2">Select Player</label>
        <select
          value={selectedPlayer}
          onChange={(e) => setSelectedPlayer(e.target.value)}
          className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="" className="text-gray-900">
            Choose a player...
          </option>
          {players.map((player) => (
            <option key={player.id} value={player.name} className="text-gray-900">
              {player.name} ({player.team} - {player.position})
            </option>
          ))}
        </select>
      </div>

      {compareMode && (
        <div>
          <label className="block text-sm font-medium mb-2">Compare With</label>
          <select
            value={player2}
            onChange={(e) => setPlayer2(e.target.value)}
            className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="" className="text-gray-900">
              Choose second player...
            </option>
            {players.map((player) => (
              <option key={player.id} value={player.name} className="text-gray-900">
                {player.name} ({player.team} - {player.position})
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-2">Opponent Team</label>
        <select
          value={opponent}
          onChange={(e) => setOpponent(e.target.value)}
          className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <option value="" className="text-gray-900">
            Choose opponent...
          </option>
          {teams.map((team) => (
            <option key={team} value={team} className="text-gray-900">
              {team}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Game Date</label>
        <input
          type="date"
          value={gameDate}
          onChange={(e) => setGameDate(e.target.value)}
          className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500"
        />
      </div>

      {!compareMode && (
        <>
          <div>
            <label className="block text-sm font-medium mb-2">Location</label>
            <div className="flex gap-4">
              <button
                onClick={() => setIsHome(true)}
                className={`flex-1 py-2 rounded-lg transition-colors ${
                  isHome ? 'bg-green-500' : 'bg-gray-600 hover:bg-gray-500'
                }`}
              >
                Home
              </button>
              <button
                onClick={() => setIsHome(false)}
                className={`flex-1 py-2 rounded-lg transition-colors ${
                  !isHome ? 'bg-blue-500' : 'bg-gray-600 hover:bg-gray-500'
                }`}
              >
                Away
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Injury Status</label>
            <select
              value={injuryStatus}
              onChange={(e) => setInjuryStatus(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="healthy" className="text-gray-900">
                Healthy
              </option>
              <option value="probable" className="text-gray-900">
                Probable
              </option>
              <option value="questionable" className="text-gray-900">
                Questionable
              </option>
              <option value="ankle" className="text-gray-900">
                Ankle Injury
              </option>
              <option value="knee" className="text-gray-900">
                Knee Injury
              </option>
              <option value="back" className="text-gray-900">
                Back Injury
              </option>
              <option value="hamstring" className="text-gray-900">
                Hamstring
              </option>
            </select>
          </div>
        </>
      )}
    </div>
  );
}

export default PredictionForm;

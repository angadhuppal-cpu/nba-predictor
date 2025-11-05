# NBA Prediction System - API Documentation

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, the API does not require authentication. For production deployment, consider implementing API keys or OAuth.

## Endpoints

### Health Check

Check if the API is running.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-04T12:00:00",
  "version": "1.0.0"
}
```

---

### Get Players

Retrieve list of all available players.

```http
GET /api/players
```

**Response:**
```json
{
  "players": [
    {
      "id": "2544",
      "name": "LeBron James",
      "team": "LAL",
      "position": "SF"
    },
    {
      "id": "1627750",
      "name": "Jayson Tatum",
      "team": "BOS",
      "position": "SF"
    }
  ]
}
```

---

### Get Teams

Retrieve list of all NBA teams.

```http
GET /api/teams
```

**Response:**
```json
{
  "teams": [
    "LAL",
    "BOS",
    "MIL",
    "PHX",
    "DEN"
  ]
}
```

---

### Predict Performance

Get performance prediction for a single player.

```http
POST /api/predict
Content-Type: application/json
```

**Request Body:**
```json
{
  "player": "LeBron James",
  "opponent": "BOS",
  "game_date": "2024-12-15",
  "is_home": true,
  "injury_status": "healthy"
}
```

**Parameters:**
- `player` (string, required): Player name
- `opponent` (string, required): Opponent team abbreviation
- `game_date` (string, required): Game date in YYYY-MM-DD format
- `is_home` (boolean, optional): Home game indicator (default: true)
- `injury_status` (string, optional): One of: healthy, ankle, knee, back, hamstring

**Response:**
```json
{
  "points": {
    "prediction": 25.3,
    "lower_bound": 21.8,
    "upper_bound": 28.8,
    "confidence": 0.78
  },
  "rebounds": {
    "prediction": 7.2,
    "lower_bound": 5.1,
    "upper_bound": 9.3,
    "confidence": 0.75
  },
  "assists": {
    "prediction": 8.1,
    "lower_bound": 6.2,
    "upper_bound": 10.0,
    "confidence": 0.72
  },
  "steals": {
    "prediction": 1.3,
    "lower_bound": 0.5,
    "upper_bound": 2.1,
    "confidence": 0.65
  },
  "blocks": {
    "prediction": 0.8,
    "lower_bound": 0.2,
    "upper_bound": 1.4,
    "confidence": 0.60
  },
  "turnovers": {
    "prediction": 3.2,
    "lower_bound": 2.0,
    "upper_bound": 4.4,
    "confidence": 0.70
  },
  "minutes": {
    "prediction": 35.5,
    "lower_bound": 32.0,
    "upper_bound": 39.0,
    "confidence": 0.80
  },
  "analysis": "📊 Moderate fatigue (0.1%) from recent games\n📈 Model confidence: 78.0%"
}
```

---

### Compare Players

Compare predicted performance of two players.

```http
POST /api/compare
Content-Type: application/json
```

**Request Body:**
```json
{
  "player1": "LeBron James",
  "player2": "Jayson Tatum",
  "opponent": "MIL",
  "game_date": "2024-12-15"
}
```

**Parameters:**
- `player1` (string, required): First player name
- `player2` (string, required): Second player name
- `opponent` (string, required): Opponent team abbreviation
- `game_date` (string, required): Game date in YYYY-MM-DD format

**Response:**
```json
{
  "player1": {
    "name": "LeBron James",
    "predictions": {
      "points": { "prediction": 25.3, ... },
      "rebounds": { "prediction": 7.2, ... }
    }
  },
  "player2": {
    "name": "Jayson Tatum",
    "predictions": {
      "points": { "prediction": 27.8, ... },
      "rebounds": { "prediction": 8.5, ... }
    }
  },
  "recommendation": "Strong recommendation: Jayson Tatum (projected 45.2 FP vs 42.1 FP)"
}
```

---

### Get Schedule

Get game schedule for a specific date.

```http
GET /api/schedule/{date}
```

**Parameters:**
- `date` (string, required): Date in YYYY-MM-DD format

**Response:**
```json
{
  "games": [
    {
      "game_id": "001",
      "date": "2024-12-15",
      "home_team": "Lakers",
      "away_team": "Warriors",
      "time": "19:30",
      "status": "Scheduled"
    }
  ]
}
```

---

### Get Injuries

Get current injury report.

```http
GET /api/injuries
```

**Response:**
```json
{
  "injuries": [
    {
      "player": "Player A",
      "team": "LAL",
      "injury": "Ankle",
      "status": "Questionable"
    },
    {
      "player": "Player B",
      "team": "BOS",
      "injury": "Knee",
      "status": "Out"
    }
  ]
}
```

---

### Get Player Recent Performance

Get player's recent game performance.

```http
GET /api/player/{player_id}/recent?games=10
```

**Parameters:**
- `player_id` (string, required): Player ID
- `games` (integer, optional): Number of recent games (default: 10)

**Response:**
```json
{
  "avg_points": 25.4,
  "avg_rebounds": 7.1,
  "avg_assists": 8.3,
  "avg_minutes": 35.2,
  "trend": "improving"
}
```

---

### Get Matchup History

Get player's performance history against a specific team.

```http
GET /api/player/{player_id}/matchup/{team}?limit=10
```

**Parameters:**
- `player_id` (string, required): Player ID
- `team` (string, required): Team abbreviation
- `limit` (integer, optional): Number of games (default: 10)

**Response:**
```json
{
  "games": [
    {
      "date": "2024-11-01",
      "points": 28,
      "rebounds": 8,
      "assists": 9,
      "minutes": 36
    }
  ]
}
```

---

### Update Data

Trigger manual data update.

```http
POST /api/update-data
```

**Response:**
```json
{
  "status": "success",
  "message": "Data updated successfully"
}
```

---

### Get System Stats

Get overall system statistics.

```http
GET /api/stats
```

**Response:**
```json
{
  "total_players": 450,
  "total_teams": 30,
  "last_update": "2024-11-04T12:00:00",
  "predictions_today": 142,
  "active_users": 15
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (missing or invalid parameters)
- `404` - Resource Not Found
- `500` - Internal Server Error

---

## Rate Limiting

Currently, no rate limiting is enforced. For production deployment, consider implementing rate limits:

- Recommended: 100 requests per minute per IP
- Prediction endpoints: 30 requests per minute per IP

---

## Examples

### Python Example

```python
import requests

# Get prediction
response = requests.post('http://localhost:5000/api/predict', json={
    'player': 'LeBron James',
    'opponent': 'BOS',
    'game_date': '2024-12-15',
    'is_home': True,
    'injury_status': 'healthy'
})

prediction = response.json()
print(f"Predicted points: {prediction['points']['prediction']}")
```

### JavaScript Example

```javascript
// Get prediction
fetch('http://localhost:5000/api/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    player: 'LeBron James',
    opponent: 'BOS',
    game_date: '2024-12-15',
    is_home: true,
    injury_status: 'healthy'
  })
})
.then(response => response.json())
.then(data => console.log('Predicted points:', data.points.prediction));
```

### cURL Example

```bash
# Get prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "player": "LeBron James",
    "opponent": "BOS",
    "game_date": "2024-12-15",
    "is_home": true,
    "injury_status": "healthy"
  }'
```

---

## Webhooks (Future)

Webhook support is planned for future releases to notify clients of:
- Data updates
- New predictions available
- Injury report changes
- Schedule updates

---

## Support

For API issues or questions:
- GitHub Issues: [Project Repository]
- Documentation: See main README.md

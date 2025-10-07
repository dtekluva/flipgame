# Bomb Flip Analytics System Documentation

## System Overview

The Bomb Flip Analytics System tracks and analyzes game performance data through a modern web dashboard and REST API. It provides real-time insights into player behavior, game outcomes, and business metrics.

**Architecture**: Frontend Dashboard + Django REST API  
**Base URL**: `https://flip.pbxl.cc`  
**Local Development**: `http://127.0.0.1:8001`

---

## API Endpoints

### 1. Get Analytics Data

**Endpoint**: `GET /api/analytics/filtered-data/`  
**Purpose**: Retrieve filtered analytics data with aggregated statistics

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_range` | string | Yes | `today`, `week`, `month`, or `custom` |
| `start_date` | string | No | YYYY-MM-DD (required if date_range=custom) |
| `end_date` | string | No | YYYY-MM-DD (required if date_range=custom) |
| `game_type` | string | No | Filter by game type (e.g., `bomb_flip`) |
| `bomb_rate` | integer | No | Filter by bomb rate (15 or 25) |

#### Sample Requests
```bash
# Get this month's data
curl "https://flip.pbxl.cc/api/analytics/filtered-data/?date_range=month"

# Get specific day data
curl "https://flip.pbxl.cc/api/analytics/filtered-data/?date_range=custom&start_date=2025-10-07&end_date=2025-10-07"

# Filter by bomb rate
curl "https://flip.pbxl.cc/api/analytics/filtered-data/?date_range=week&bomb_rate=15"
```

#### Sample Response
```json
{
  "overall": {
    "total_sessions": 12,
    "total_stakes": 1800.0,
    "total_payouts": 1945.0,
    "total_wins": 5,
    "total_losses": 5,
    "total_perfect_games": 2,
    "house_profit": -145.0,
    "house_edge": -8.06,
    "overall_win_rate": 41.67
  },
  "combinations": [
    {
      "game_type": "bomb_flip",
      "bomb_rate": 15,
      "total_sessions": 8,
      "wins": 4,
      "losses": 2,
      "perfect_games": 2,
      "win_rate": 50.0,
      "avg_multiplier": 1.65,
      "total_stakes": 1200.0,
      "total_payouts": 1665.0,
      "house_profit": -465.0,
      "house_edge": "-38.75",
      "recent_sessions": [...]
    }
  ],
  "filters": {
    "date_range": "month",
    "start_date": "2025-09-07T15:18:04.521684+00:00",
    "end_date": "2025-10-07T15:18:04.521684+00:00"
  }
}
```

**Status Codes**: 200 (Success), 400 (Bad Request), 500 (Server Error)

### 2. Submit Game Results

**Endpoint**: `POST /api/analytics/submit/`  
**Purpose**: Submit new game analytics data from production servers

#### Request Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "game_type": "bomb_flip",
  "player_name": "Alice",
  "stake_amount": 100.00,
  "winning_amount": 125.00,
  "multiplier": 1.25,
  "bomb_rate": 15,
  "cards_flipped": 5,
  "game_outcome": "WIN",
  "session_id": "optional-session-id"
}
```

#### Sample Request
```bash
curl -X POST "https://flip.pbxl.cc/api/analytics/submit/" \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "bomb_flip",
    "player_name": "Alice",
    "stake_amount": 100.00,
    "winning_amount": 125.00,
    "multiplier": 1.25,
    "bomb_rate": 15,
    "cards_flipped": 5,
    "game_outcome": "WIN"
  }'
```

#### Sample Response
```json
{
  "status": "success",
  "message": "Game analytics submitted successfully",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Status Codes**: 201 (Created), 400 (Bad Request), 500 (Server Error)

---

## Data Model

### GameAnalytics Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_type` | string | Yes | Type of game (e.g., "bomb_flip") |
| `player_name` | string | No | Player's display name |
| `stake_amount` | decimal | Yes | Amount wagered (₦) |
| `winning_amount` | decimal | Yes | Amount won (₦, 0 for losses) |
| `multiplier` | decimal | Yes | Final multiplier achieved |
| `bomb_rate` | integer | Yes | Bomb percentage (15 or 25) |
| `cards_flipped` | integer | Yes | Number of safe cards revealed |
| `game_outcome` | string | Yes | "WIN", "LOSS", or "PERFECT" |
| `session_id` | string | No | Optional session identifier |
| `created_at` | datetime | Auto | Timestamp (auto-generated) |

---

## Dashboard Usage

### Access
- **Production**: `https://flip.pbxl.cc/analytics_filtered.html`
- **Local**: Open `analytics_filtered.html` in browser

### Filters
1. **Date Range**: Today, This Week, This Month, Specific Day, Custom Range
2. **Game Type**: Filter by game variant
3. **Bomb Rate**: Filter by difficulty (15% or 25%)

### Statistics Displayed
- **Overall Stats**: Sessions, stakes, profit, win rates
- **Combinations**: Performance by game type and bomb rate
- **Recent Sessions**: Individual game records with outcomes

---

## Setup & Deployment

### Backend Setup
```bash
# Install dependencies
cd backend
pip install django djangorestframework

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver 8001
```

### Frontend Access
```bash
# Open dashboard
open analytics_filtered.html
# or serve via web server
python -m http.server 8080
```

### Dependencies
- Python 3.8+
- Django 4.2+
- Django REST Framework
- Modern web browser

---

## Integration Guide

### Production Integration
```python
import requests

# Submit game result
def submit_game_analytics(game_data):
    response = requests.post(
        "https://flip.pbxl.cc/api/analytics/submit/",
        json=game_data,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

# Example usage
game_result = {
    "game_type": "bomb_flip",
    "player_name": "Player123",
    "stake_amount": 200.00,
    "winning_amount": 0.00,
    "multiplier": 1.00,
    "bomb_rate": 25,
    "cards_flipped": 3,
    "game_outcome": "LOSS"
}

result = submit_game_analytics(game_result)
```

### Error Handling
```python
try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    # Log error and retry logic
    print(f"Analytics submission failed: {e}")
```

### Best Practices
- Submit data immediately after game completion
- Include all required fields
- Handle network failures gracefully
- Use meaningful player names for better analytics
- Set appropriate timeouts (10-30 seconds)

---

## Quick Reference

### Common API Calls
```bash
# Today's data
curl "https://flip.pbxl.cc/api/analytics/filtered-data/?date_range=today"

# Specific day
curl "https://flip.pbxl.cc/api/analytics/filtered-data/?date_range=custom&start_date=2025-10-07&end_date=2025-10-07"

# Submit game
curl -X POST "https://flip.pbxl.cc/api/analytics/submit/" \
  -H "Content-Type: application/json" \
  -d '{"game_type":"bomb_flip","stake_amount":100,"winning_amount":0,"multiplier":1,"bomb_rate":15,"cards_flipped":2,"game_outcome":"LOSS"}'
```

### Valid Values
- **game_outcome**: "WIN", "LOSS", "PERFECT"
- **bomb_rate**: 15, 25
- **stake_amount**: 100.00, 200.00
- **date_range**: "today", "week", "month", "custom"

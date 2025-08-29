# 💣 Bomb Flip Betting Game - Django Backend

This Django app provides a complete gameplay logging system for the Bomb Flip Betting game.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations game_ledger
python manage.py migrate
```

### 3. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver
```

## 📊 Models

### GameSession
Tracks individual game sessions with betting information:
- **user_id**: Player identifier
- **starting_balance**: Wallet balance at game start
- **stake**: Amount wagered
- **grid_size**: Game grid dimensions (3-7)
- **bomb_probability**: Bomb chance percentage (5-50%)
- **status**: ACTIVE, CASHED_OUT, or BOMB_HIT
- **created_at/ended_at**: Session timestamps

### GameEvent
Logs every action within a game session:
- **event_type**: GAME_STARTED, FLIP, CASHOUT, BOMB_HIT
- **amount**: Money involved (winnings, stake, etc.)
- **balance**: Player balance after event
- **multiplier**: Current game multiplier
- **cell_position**: Grid position (e.g., "2-3")
- **timestamp**: When event occurred

## 🔌 API Endpoints

### Start New Game
```http
POST /api/game/start/
Content-Type: application/json

{
    "user_id": "player123",
    "starting_balance": 1000.00,
    "grid_size": 5,
    "bomb_probability": 20.0,
    "stake": 100.00
}
```

**Response:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "ACTIVE"
}
```

### Log Game Event
```http
POST /api/game/event/
Content-Type: application/json

{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "FLIP",
    "amount": null,
    "balance": 900.00,
    "multiplier": 1.1,
    "cell_position": "2-3"
}
```

### Get Session Details
```http
GET /api/game/session/{session_id}/
```

### Get User Sessions
```http
GET /api/game/user/{user_id}/sessions/
```

## 🎮 Game Logic Integration

The backend tracks every aspect of gameplay:

1. **Game Start**: Creates session + GAME_STARTED event
2. **Each Card Flip**: Logs FLIP event with position and multiplier
3. **Cash Out**: Logs CASHOUT event + updates session status
4. **Bomb Hit**: Logs BOMB_HIT event + ends session

## 🛠 Admin Interface

Access at `/admin/` to view:
- **Game Sessions**: Filter by status, search by user
- **Game Events**: Inline display within sessions
- **Complete Audit Trail**: Every game action logged

## 🔧 Configuration

Easy to modify in `models.py`:
- **Currency precision**: DecimalField(max_digits=12, decimal_places=2)
- **Grid size limits**: 3-10 in serializer validation
- **Bomb probability**: 5-50% range
- **Event types**: Easily extensible choices

## 📈 Analytics Potential

The logging system enables:
- **Player behavior analysis**
- **Risk/reward pattern tracking**
- **Game balance optimization**
- **Revenue/loss calculations**
- **Session duration analytics**

Perfect for understanding how players interact with your betting game! 🎯

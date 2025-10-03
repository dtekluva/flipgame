# 💣 Bomb Flip Betting Game 💰

A thrilling lottery-style betting game where players flip numbered cards to avoid bombs and win multiplied rewards!

## 🎮 How to Play

### Game Objective
Flip as many safe cards as possible without hitting a bomb to multiply your stake and win money!

## 🎯 Game Rules

### 1. **Starting the Game**
- **Stake Options**: ₦100 or ₦200 (fixed amounts)
- **Bomb Rate Options**: 15% or 25% (fixed rates)
- **Starting Wallet**: ₦10,000
- **Grid Options**: 3x3, 4x4, 5x5, 6x6, or 7x7
- **Player Name**: Enter your name or get a random one

### 2. **Card System**
- Each card is numbered (1, 2, 3, etc.) like lottery tickets
- Cards are either **SAFE** (✅) or **BOMBS** (💣)
- You must flip cards one by one
- Once flipped, cards cannot be unflipped

### 3. **Bomb Probability (Simplified System)**
The game now uses a simplified system with fixed bomb rates for better predictability:

#### **Available Combinations:**
| Stake Amount | Bomb Rate | Risk Level | Strategy |
|--------------|-----------|------------|----------|
| **₦100** | **15%** | Low Risk | Conservative play, good for beginners |
| **₦100** | **25%** | Medium Risk | Balanced risk/reward |
| **₦200** | **15%** | Low Risk | Higher stakes, safer odds |
| **₦200** | **25%** | High Risk | Maximum risk/reward potential |

#### **Benefits of Fixed System:**
- **Predictable**: No randomization, you know exactly what you're getting
- **Strategic**: Choose your risk level based on your comfort
- **Transparent**: Clear understanding of odds before you play

## 💣 Detailed Bomb Flip Logic & Algorithm

### **Phase 1: Dynamic Bomb Rate Calculation**

#### **Step 1: Exponential Base Rate Formula**
```javascript
function calculateDynamicBombProbability(stakeAmount) {
    const minBombRate = 3;  // 3% minimum
    const maxBombRate = 40; // 40% maximum
    const minStake = 200;   // Starting stake
    const maxStake = 5000;  // Maximum progression stake

    if (stakeAmount >= maxStake) {
        return maxBombRate; // Cap at 40%
    }

    // Calculate exponential progression
    const stakeRatio = (stakeAmount - minStake) / (maxStake - minStake);
    const exponentialRatio = Math.pow(stakeRatio, 1.6);
    const baseRate = minBombRate + (exponentialRatio * (maxBombRate - minBombRate));

    return baseRate;
}
```

**Mathematical Explanation:**
- **Linear vs Exponential**: Linear would be boring (₦1000=8%, ₦2000=16%)
- **Exponential Power 1.6**: Creates steeper curve at higher stakes
- **Result**: Low stakes very safe, high stakes dramatically riskier

#### **Step 2: Direct Rate Application**
```javascript
function applyBombRate(selectedRate) {
    // No randomization - use exactly what player selected
    return selectedRate; // 15% or 25% exactly
}
```

**Why Fixed Rates?**
- **Predictable**: Players know exactly what they're getting
- **Strategic**: Allows for informed decision making
- **Transparent**: No hidden calculations or variations

### **Phase 2: Board Generation Algorithm**

#### **Step 1: Grid Structure Creation**
```javascript
function createBoard(gridSize) {
    board = [];
    for (let row = 0; row < gridSize; row++) {
        board[row] = [];
        for (let col = 0; col < gridSize; col++) {
            board[row][col] = {
                isBomb: false,      // Default: safe
                isFlipped: false,   // Default: hidden
                row: row,           // Position tracking
                col: col,           // Position tracking
                cardNumber: (row * gridSize) + col + 1 // Lottery number
            };
        }
    }
}
```

#### **Step 2: Independent Bomb Placement**
```javascript
function placeBombs(finalBombRate) {
    let bombsPlaced = 0;

    for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
            // Each cell independently evaluated
            const randomRoll = Math.random() * 100;

            if (randomRoll < finalBombRate) {
                board[row][col].isBomb = true;
                bombsPlaced++;
            }
        }
    }

    console.log(`Bombs placed: ${bombsPlaced}/${gridSize * gridSize} cells`);
    return bombsPlaced;
}
```

**Critical Understanding:**
- **Independent rolls**: Each of 25 cards gets separate random number
- **No bomb quotas**: Game doesn't force exact bomb counts
- **Pure probability**: 20% rate means each card has 20% bomb chance
- **Variance possible**: Could get 0 bombs or 15 bombs (rare but possible)

### 4. **Multiplier System**
- **Starting Multiplier**: 1.00x
- **Increment**: +0.05x per safe card flipped
- **Example**: 1.00x → 1.05x → 1.10x → 1.15x → 1.20x...

### 5. **Cashout Rules**
- **Minimum Requirement**: Must flip at least 5 safe cards before cashing out
- **Early Cashout Attempt**: Shows warning message with remaining flips needed
- **Cashout Formula**: Winnings = Stake × Current Multiplier
- **Profit**: Winnings - Original Stake

### 6. **Winning Conditions**

#### **💰 Cash Out (Player Choice)**
- Click "Cash Out" after flipping 5+ safe cards
- Receive: Stake × Current Multiplier
- Game ends successfully

#### **🎉 Perfect Game (All Safe Cards)**
- Flip all safe cards without hitting any bombs
- Automatic cashout at maximum multiplier
- Bonus celebration with special sound effects

#### **💥 Bomb Hit (Game Over)**
- Hit any bomb = immediate game over
- Lose entire stake amount
- All remaining bombs are revealed

## 🎲 Game Features

### **Lottery-Style Experience**
- **Numbered Cards**: Each card displays a number (1-25 for 5x5 grid)
- **Fancy Fonts**: Premium Orbitron font for numbers, Fredoka One for titles
- **Visual Effects**: Hover effects, animations, and premium styling

### **Audio System**
- **Safe Card**: Pleasant "ding" sound
- **Bomb Hit**: Explosion sound effect
- **Perfect Game**: Celebratory "hurray" sound
- **Sound Toggle**: Mute/unmute button available

### **Real-Time Information**
- **Current Stake**: Amount you bet this round
- **Current Multiplier**: Your current payout multiplier
- **Potential Winnings**: Stake × Current Multiplier
- **Safe Cards**: Number of safe cards flipped
- **Bomb Rate**: Live calculation based on your stake

## 📱 Technical Features

### **Responsive Design**
- Works on desktop, tablet, and mobile devices
- Optimized layouts for different screen sizes
- Touch-friendly interface

### **Backend Integration**
- Game sessions tracked on server
- Event logging for all player actions
- Offline mode fallback if server unavailable

### **Progressive Web App**
- Fast loading and smooth animations
- Modern web technologies
- Cross-platform compatibility

## 🎯 Strategy Tips

### **Risk Management**
1. **Start Small**: Begin with lower stakes to learn the game
2. **Watch Bomb Rates**: Higher stakes = higher bomb probability
3. **Know When to Cash Out**: Don't get greedy - secure profits early
4. **Minimum Flips**: Remember you need 5 safe cards minimum

### **Stake Strategy**
- **Low Stakes (₦200-₦500)**: Very safe, good for beginners
- **Medium Stakes (₦500-₦2000)**: Balanced risk/reward
- **High Stakes (₦2000-₦5000)**: High risk, high reward potential

### **Multiplier Building**
- Each safe card adds 0.05x to your multiplier
- 10 safe cards = 1.50x multiplier
- 20 safe cards = 2.00x multiplier
- Perfect game varies by grid size and bomb placement

## ⚠️ Important Notes

- **Gambling Responsibly**: Only bet what you can afford to lose
- **Fixed Rates**: Bomb rates are exactly as selected (15% or 25%)
- **No Guarantees**: Past results don't predict future outcomes
- **Wallet Management**: Game ends when wallet drops below minimum stake

## 🚀 Getting Started

1. Enter your player name (or use auto-generated name)
2. Choose your stake amount (₦200-₦1000)
3. Select grid size (5x5 recommended)
4. Click "Start Game"
5. Click numbered cards to flip them
6. Cash out when you're satisfied with your multiplier!

---

**Good luck and may the odds be in your favor!** 🍀🎰

## 🛠 Technical Setup

### Frontend
- Open `index.html` in a web browser
- No additional setup required for basic gameplay

### Backend (Optional)
- See `backend/README.md` for Django server setup
- Enables game session tracking and analytics
- Fallback to offline mode if server unavailable

### Analytics Dashboard
- Access at `analytics.html` to view real-time game statistics
- Breakdown by stake amount (₦100/₦200) and bomb rate (15%/25%)
- Shows win rates, house edge, and recent sessions
- Auto-refreshes every 30 seconds
- Click the 📊 button in the game to access analytics

---

## 💣 SIMPLIFIED BOMB FLIP ALGORITHM

### **Phase 1: Fixed Bomb Rate Selection**

The game now uses a simplified system where players select from predefined combinations:

```javascript
// Available combinations
const GAME_COMBINATIONS = [
    { stake: 100, bombRate: 15 },  // Low risk, low stake
    { stake: 100, bombRate: 25 },  // Medium risk, low stake
    { stake: 200, bombRate: 15 },  // Low risk, high stake
    { stake: 200, bombRate: 25 }   // High risk, high stake
];

// No calculation needed - direct selection
function getBombRate(selectedStake, selectedBombRate) {
    return selectedBombRate; // Exactly what the player chose
}
```

### **Phase 2: Board Generation Process**

#### **Independent Cell Evaluation**
```javascript
function placeBombs(finalBombRate, gridSize) {
    let bombsPlaced = 0;

    for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
            // Each cell gets independent random roll
            const randomRoll = Math.random() * 100;

            if (randomRoll < finalBombRate) {
                board[row][col].isBomb = true;
                bombsPlaced++;
            }
        }
    }

    return bombsPlaced;
}
```

**Critical Understanding:**
- **No bomb quotas**: Game doesn't guarantee exact bomb counts
- **Pure probability**: Each cell has independent bomb chance
- **Variance expected**: Actual bombs can differ from expected

### **Phase 3: Detailed Probability Examples**

#### **5x5 Grid (25 cards) Probability Table**

| Stake | Base Rate | Random Range | Expected Bombs | Likely Range | Safe Cards |
|-------|-----------|--------------|----------------|--------------|------------|
| ₦200 | 3.0% | 1-8% | 0.75 | 0-2 | 23-25 |
| ₦300 | 4.1% | 1-9% | 1.0 | 0-3 | 22-25 |
| ₦500 | 5.2% | 0.2-10.2% | 1.3 | 0-3 | 22-25 |
| ₦750 | 7.8% | 2.8-12.8% | 1.95 | 1-4 | 21-24 |
| ₦1000 | 9.8% | 4.8-14.8% | 2.45 | 1-4 | 21-24 |
| ₦1500 | 14.2% | 9.2-19.2% | 3.55 | 2-5 | 20-23 |
| ₦2000 | 18.5% | 13.5-23.5% | 4.6 | 3-6 | 19-22 |
| ₦2500 | 22.7% | 17.7-27.7% | 5.7 | 4-7 | 18-21 |
| ₦3000 | 26.8% | 21.8-31.8% | 6.7 | 5-8 | 17-20 |
| ₦4000 | 33.8% | 28.8-38.8% | 8.45 | 7-10 | 15-18 |
| ₦5000 | 40.0% | 35-45% | 10 | 8-12 | 13-17 |

### **Phase 4: Card Flip Processing**

#### **Click Validation Sequence**
```javascript
function handleCardClick(row, col) {
    // Validation checks
    if (!gameActive) return;        // Game must be running
    if (gameOver) return;           // Game must not be over
    if (cell.isFlipped) return;     // Card must not be flipped

    // Process the flip
    processCardFlip(row, col);
}
```

#### **Safe Card Logic**
```javascript
function processSafeCard(cell, cardElement) {
    // Update cell state
    cell.isFlipped = true;

    // Update visual
    cardElement.textContent = '✅';
    cardElement.classList.add('safe', 'flipped');

    // Update game state
    safeCardsFlipped++;
    currentMultiplier += 0.05;

    // Audio feedback
    playDingSound();

    // UI updates
    updateGameInfo();

    // Check win condition
    if (safeCardsFlipped === getTotalSafeCells()) {
        triggerPerfectGame();
    }
}
```

#### **Bomb Hit Logic**
```javascript
function processBombHit(cell, cardElement) {
    // Update cell state
    cell.isFlipped = true;

    // Update visual
    cardElement.textContent = '💣';
    cardElement.classList.add('bomb', 'flipped');

    // End game
    gameOver = true;
    gameActive = false;

    // Audio feedback
    playExplosionSound();

    // Reveal all bombs
    revealAllBombs();

    // Show lose message
    showMessage(`💥 BOOM! Lost ₦${currentStake}!`, 'lose');

    // Stake already deducted from wallet at game start
}
```

### 4. **Multiplier System**

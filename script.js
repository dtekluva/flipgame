class BombFlipBettingGame {
    constructor() {
        // Game configuration (easily configurable)
        this.config = {
            startingMultiplier: 1.0,
            multiplierIncrement: 0.1,
            startingWallet: 1000,
            minStake: 1,
            maxStake: 1000,
            apiBaseUrl: 'http://127.0.0.1:8000/api'
        };

        // Game state
        this.wallet = this.config.startingWallet;
        this.currentStake = 0;
        this.currentMultiplier = this.config.startingMultiplier;
        this.safeCardsFlipped = 0;
        this.gameActive = false;
        this.gameOver = false;

        // Game board
        this.board = [];
        this.gridSize = 5;
        this.bombProbability = 20; // percentage

        // Backend integration
        this.currentSessionId = null;
        this.userName = '';
        this.userId = this.generateUserId();
        this.offlineMode = false;

        // Initialize audio
        this.initAudio();

        // DOM elements
        this.initDOMElements();
        this.initEventListeners();
        this.updateWalletDisplay();

        // Debug: Monitor game board changes
        this.setupGameBoardMonitor();
    }

    initAudio() {
        // Create audio context for generating sounds
        this.audioContext = null;

        // Initialize audio context on first user interaction
        this.audioInitialized = false;

        // Sound settings
        this.soundEnabled = true;
    }

    initAudioContext() {
        if (!this.audioInitialized) {
            try {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                this.audioInitialized = true;
            } catch (e) {
                console.log('Audio not supported');
                this.soundEnabled = false;
            }
        }
    }

    playDingSound() {
        if (!this.soundEnabled) return;

        this.initAudioContext();
        if (!this.audioContext) return;

        // Create a pleasant ding sound
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        // Ding sound: high frequency with quick decay
        oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(1200, this.audioContext.currentTime + 0.1);

        gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);

        oscillator.type = 'sine';
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.3);
    }

    playExplosionSound() {
        if (!this.soundEnabled) return;

        this.initAudioContext();
        if (!this.audioContext) return;

        // Create an electronic explosion sound
        const oscillator1 = this.audioContext.createOscillator();
        const oscillator2 = this.audioContext.createOscillator();
        const noiseBuffer = this.createNoiseBuffer();
        const noiseSource = this.audioContext.createBufferSource();

        const gainNode1 = this.audioContext.createGain();
        const gainNode2 = this.audioContext.createGain();
        const noiseGain = this.audioContext.createGain();
        const masterGain = this.audioContext.createGain();

        // Connect nodes
        oscillator1.connect(gainNode1);
        oscillator2.connect(gainNode2);
        noiseSource.connect(noiseGain);

        gainNode1.connect(masterGain);
        gainNode2.connect(masterGain);
        noiseGain.connect(masterGain);
        masterGain.connect(this.audioContext.destination);

        // Set up explosion sound characteristics
        const now = this.audioContext.currentTime;

        // Low frequency rumble
        oscillator1.frequency.setValueAtTime(60, now);
        oscillator1.frequency.exponentialRampToValueAtTime(30, now + 0.5);
        oscillator1.type = 'sawtooth';

        // High frequency crack
        oscillator2.frequency.setValueAtTime(1000, now);
        oscillator2.frequency.exponentialRampToValueAtTime(100, now + 0.2);
        oscillator2.type = 'square';

        // Noise for texture
        noiseSource.buffer = noiseBuffer;

        // Envelope for explosion
        masterGain.gain.setValueAtTime(0.5, now);
        masterGain.gain.exponentialRampToValueAtTime(0.01, now + 0.8);

        gainNode1.gain.setValueAtTime(0.7, now);
        gainNode1.gain.exponentialRampToValueAtTime(0.01, now + 0.5);

        gainNode2.gain.setValueAtTime(0.4, now);
        gainNode2.gain.exponentialRampToValueAtTime(0.01, now + 0.2);

        noiseGain.gain.setValueAtTime(0.3, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);

        // Start and stop
        oscillator1.start(now);
        oscillator2.start(now);
        noiseSource.start(now);

        oscillator1.stop(now + 0.8);
        oscillator2.stop(now + 0.8);
        noiseSource.stop(now + 0.8);
    }

    playHurraySound() {
        if (!this.soundEnabled) return;

        this.initAudioContext();
        if (!this.audioContext) return;

        // Create a celebratory hurray sound with multiple ascending tones
        const now = this.audioContext.currentTime;
        const masterGain = this.audioContext.createGain();
        masterGain.connect(this.audioContext.destination);

        // Create multiple oscillators for a chord progression
        const frequencies = [
            { freq: 523, delay: 0 },     // C5
            { freq: 659, delay: 0.1 },   // E5
            { freq: 784, delay: 0.2 },   // G5
            { freq: 1047, delay: 0.3 }   // C6
        ];

        frequencies.forEach(({ freq, delay }) => {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(masterGain);

            // Ascending celebratory tone
            oscillator.frequency.setValueAtTime(freq, now + delay);
            oscillator.frequency.exponentialRampToValueAtTime(freq * 1.2, now + delay + 0.3);
            oscillator.type = 'sine';

            // Envelope for each note
            gainNode.gain.setValueAtTime(0, now + delay);
            gainNode.gain.linearRampToValueAtTime(0.2, now + delay + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + delay + 0.4);

            oscillator.start(now + delay);
            oscillator.stop(now + delay + 0.4);
        });

        // Add some sparkle with higher frequencies
        for (let i = 0; i < 3; i++) {
            const sparkle = this.audioContext.createOscillator();
            const sparkleGain = this.audioContext.createGain();

            sparkle.connect(sparkleGain);
            sparkleGain.connect(masterGain);

            const sparkleDelay = 0.5 + (i * 0.1);
            sparkle.frequency.setValueAtTime(1500 + (i * 200), now + sparkleDelay);
            sparkle.type = 'sine';

            sparkleGain.gain.setValueAtTime(0.1, now + sparkleDelay);
            sparkleGain.gain.exponentialRampToValueAtTime(0.01, now + sparkleDelay + 0.2);

            sparkle.start(now + sparkleDelay);
            sparkle.stop(now + sparkleDelay + 0.2);
        }

        // Master envelope
        masterGain.gain.setValueAtTime(0.8, now);
        masterGain.gain.exponentialRampToValueAtTime(0.01, now + 1.0);
    }

    createNoiseBuffer() {
        const bufferSize = this.audioContext.sampleRate * 0.3; // 0.3 seconds of noise
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }

        return buffer;
    }

    initDOMElements() {
        this.gameBoard = document.getElementById('game-board');
        this.walletElement = document.getElementById('wallet-amount');
        this.winningsDisplay = document.getElementById('winnings-display');
        this.lastWinningsElement = document.getElementById('last-winnings');
        this.gameSetup = document.getElementById('game-setup');
        this.gameInfo = document.getElementById('game-info');
        this.gameMessageElement = document.getElementById('game-message');

        // Setup elements
        this.usernameInput = document.getElementById('username-input');
        this.stakeInput = document.getElementById('stake-input');
        this.gridSizeSelect = document.getElementById('grid-size');
        this.bombProbabilitySelect = document.getElementById('bomb-probability');
        this.startGameBtn = document.getElementById('start-game-btn');

        // Game info elements
        this.currentPlayerElement = document.getElementById('current-player');
        this.currentStakeElement = document.getElementById('current-stake');
        this.currentMultiplierElement = document.getElementById('current-multiplier');
        this.potentialWinningsElement = document.getElementById('potential-winnings');
        this.safeCardsElement = document.getElementById('safe-cards');
        this.cashoutBtn = document.getElementById('cashout-btn');
        this.resetGameBtn = document.getElementById('reset-game-btn');
        this.soundToggleBtn = document.getElementById('sound-toggle-btn');
    }

    initEventListeners() {
        this.startGameBtn.addEventListener('click', () => {
            console.log('🎮 Start Game button clicked');
            this.startGame();
        });
        this.cashoutBtn.addEventListener('click', () => {
            console.log('💰 Cash Out button clicked');
            this.cashOut();
        });
        this.resetGameBtn.addEventListener('click', () => {
            console.log('🔄 Reset Game button clicked');
            this.resetGame();
        });
        this.soundToggleBtn.addEventListener('click', () => this.toggleSound());

        // Update max stake when wallet changes
        this.stakeInput.addEventListener('input', () => {
            const maxStake = Math.min(this.wallet, this.config.maxStake);
            this.stakeInput.max = maxStake;
        });

        // Generate random username if empty
        this.usernameInput.addEventListener('focus', () => {
            if (!this.usernameInput.value.trim()) {
                this.usernameInput.value = this.generateRandomUsername();
            }
        });
    }

    generateUserId() {
        // Generate a simple user ID for demo purposes
        return 'player_' + Math.random().toString(36).substring(2, 11);
    }

    generateRandomUsername() {
        const adjectives = ['Lucky', 'Bold', 'Swift', 'Clever', 'Brave', 'Sharp', 'Quick', 'Smart'];
        const nouns = ['Player', 'Gamer', 'Winner', 'Champion', 'Hero', 'Star', 'Pro', 'Master'];
        const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
        const noun = nouns[Math.floor(Math.random() * nouns.length)];
        const number = Math.floor(Math.random() * 999) + 1;
        return `${adjective}${noun}${number}`;
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const url = `${this.config.apiBaseUrl}${endpoint}`;
        console.log(`🌐 API Call: ${method} ${url}`);

        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                options.body = JSON.stringify(data);
                console.log('📤 Request body:', JSON.stringify(data, null, 2));
            }

            console.log('🚀 Making fetch request...');
            const response = await fetch(url, options);
            console.log('📡 Response status:', response.status, response.statusText);

            if (!response.ok) {
                const errorData = await response.text();
                console.error('❌ API Error Response:', errorData);
                try {
                    const jsonError = JSON.parse(errorData);
                    return { success: false, error: jsonError };
                } catch {
                    return { success: false, error: errorData };
                }
            }

            const responseData = await response.json();
            console.log('✅ API Success Response:', responseData);
            return responseData;

        } catch (error) {
            console.error('💥 Network Error:', error);
            return { success: false, error: error.message };
        }
    }

    async startGame() {
        try {
            console.log('🎮 Starting game...');

            // Get and validate username
            this.userName = this.usernameInput.value.trim();
            if (!this.userName) {
                this.userName = this.generateRandomUsername();
                this.usernameInput.value = this.userName;
            }
            console.log('👤 Player name:', this.userName);

            // Validate stake
            const stakeAmount = parseFloat(this.stakeInput.value);
            console.log('💰 Stake amount:', stakeAmount, 'Wallet:', this.wallet);

            if (isNaN(stakeAmount) || stakeAmount < this.config.minStake || stakeAmount > this.wallet) {
                console.error('❌ Invalid stake amount');
                this.showMessage(`Invalid stake! Must be between ₦${this.config.minStake} and ₦${this.wallet}`, 'lose');
                return;
            }

            // Get game settings
            this.gridSize = parseInt(this.gridSizeSelect.value);
            this.bombProbability = parseInt(this.bombProbabilitySelect.value);
            console.log('⚙️ Game settings:', { gridSize: this.gridSize, bombProbability: this.bombProbability });

            // Initialize game state FIRST (don't wait for backend)
            this.currentStake = stakeAmount;
            this.wallet -= stakeAmount;
            this.currentMultiplier = this.config.startingMultiplier;
            this.safeCardsFlipped = 0;
            this.gameActive = true;
            this.gameOver = false;

            // Create and render board
            this.createBoard();
            this.placeBombs();
            this.renderBoard();

            // Update UI
            console.log('🎨 Updating UI...');
            this.gameSetup.classList.add('hidden');
            this.gameInfo.classList.remove('hidden');
            this.gameMessageElement.classList.add('hidden');
            this.updateGameInfo();
            this.updatePlayerInfo();
            this.updateWalletDisplay();
            console.log('✅ Game started successfully!');

            // Try to start backend session (non-blocking)
            this.startBackendSession(stakeAmount);

        } catch (error) {
            console.error('💥 Error starting game:', error);
            this.showMessage('Error starting game. Please try again.', 'lose');

            // Reset game state on error
            this.gameActive = false;
            this.gameOver = false;
            this.currentSessionId = null;
        }
    }

    async startBackendSession(stakeAmount) {
        try {
            const gameData = {
                user_id: this.userId,
                username: this.userName,
                starting_balance: parseFloat((this.wallet + stakeAmount).toFixed(2)), // Original wallet before deduction
                grid_size: this.gridSize,
                bomb_probability: parseFloat(this.bombProbability.toFixed(2)),
                stake: parseFloat(stakeAmount.toFixed(2))
            };

            console.log('🌐 Calling backend API...');
            const response = await this.apiCall('/game/start/', 'POST', gameData);
            console.log('📡 API Response:', response);

            if (response && response.session_id) {
                this.currentSessionId = response.session_id;
                this.offlineMode = false;
                console.log('✅ Backend session started:', this.currentSessionId);
            } else {
                throw new Error('No session ID received');
            }
        } catch (error) {
            this.offlineMode = true;
            console.warn('⚠️ Backend unavailable - playing offline:', error.message);
        }
    }

    createBoard() {
        console.log('🏗️ Creating board...', { gridSize: this.gridSize });
        this.board = [];

        for (let row = 0; row < this.gridSize; row++) {
            this.board[row] = [];
            for (let col = 0; col < this.gridSize; col++) {
                this.board[row][col] = {
                    isBomb: false,
                    isFlipped: false,
                    row: row,
                    col: col
                };
            }
        }

        console.log(`✅ Board created: ${this.gridSize}x${this.gridSize} = ${this.gridSize * this.gridSize} cells`);
    }

    placeBombs() {
        console.log('💣 Placing bombs...', { bombProbability: this.bombProbability });
        let bombsPlaced = 0;

        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                // Each cell has bombProbability% chance of being a bomb
                if (Math.random() * 100 < this.bombProbability) {
                    this.board[row][col].isBomb = true;
                    bombsPlaced++;
                }
            }
        }

        console.log(`💣 Bombs placed: ${bombsPlaced} out of ${this.gridSize * this.gridSize} cells`);
    }

    renderBoard() {
        console.log('🎨 Rendering board...', { gridSize: this.gridSize });

        if (!this.gameBoard) {
            console.error('❌ Game board element not found!');
            return;
        }

        // Clear existing content
        this.gameBoard.innerHTML = '';

        // Validate grid size
        if (!this.gridSize || this.gridSize < 3 || this.gridSize > 10) {
            console.error('❌ Invalid grid size:', this.gridSize);
            this.gridSize = 5; // fallback
        }

        // Set grid layout
        this.gameBoard.style.gridTemplateColumns = `repeat(${this.gridSize}, 1fr)`;
        this.gameBoard.style.gridTemplateRows = `repeat(${this.gridSize}, 1fr)`;
        this.gameBoard.style.display = 'grid'; // Ensure it's visible

        let cardsCreated = 0;
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                try {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.dataset.row = row;
                    card.dataset.col = col;

                    card.addEventListener('click', () => this.flipCard(row, col));

                    this.gameBoard.appendChild(card);
                    cardsCreated++;
                } catch (error) {
                    console.error('❌ Error creating card:', error);
                }
            }
        }

        console.log(`✅ Board rendered: ${cardsCreated} cards created`);
        console.log('🎯 Game board element:', this.gameBoard);
        console.log('🎯 Game board display:', window.getComputedStyle(this.gameBoard).display);
    }

    async flipCard(row, col) {
        if (!this.gameActive || this.gameOver || this.board[row][col].isFlipped) {
            return;
        }

        const cell = this.board[row][col];
        cell.isFlipped = true;

        const cardElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        cardElement.classList.add('flipped');

        const cellPosition = `${row}-${col}`;

        if (cell.isBomb) {
            // Hit a bomb - game over
            cardElement.textContent = '💣';
            cardElement.classList.add('bomb');
            this.gameOver = true;
            this.gameActive = false;

            // Play explosion sound
            this.playExplosionSound();

            // Log bomb hit event
            await this.logGameEvent('BOMB_HIT', {
                cell_position: cellPosition,
                balance: parseFloat(this.wallet.toFixed(2)),
                multiplier: parseFloat(this.currentMultiplier.toFixed(2))
            });

            this.showMessage(`💥 BOOM! You hit a bomb and lost ₦${this.currentStake.toFixed(2)}!`, 'lose');
            this.revealAllBombs();

        } else {
            // Safe card - increase multiplier
            cardElement.textContent = '✅';
            cardElement.classList.add('safe');
            this.safeCardsFlipped++;
            this.currentMultiplier += this.config.multiplierIncrement;

            // Play ding sound
            this.playDingSound();

            // Log flip event
            await this.logGameEvent('FLIP', {
                cell_position: cellPosition,
                balance: parseFloat(this.wallet.toFixed(2)),
                multiplier: parseFloat(this.currentMultiplier.toFixed(2))
            });

            this.updateGameInfo();

            // Check if all safe cards are flipped (perfect game)
            if (this.getAllSafeCards().length === this.safeCardsFlipped) {
                this.gameActive = false;
                const winnings = this.currentStake * this.currentMultiplier;
                const profit = winnings - this.currentStake;
                this.wallet += winnings;

                // Log perfect game cashout
                await this.logGameEvent('CASHOUT', {
                    amount: parseFloat(winnings.toFixed(2)),
                    balance: parseFloat(this.wallet.toFixed(2)),
                    multiplier: parseFloat(this.currentMultiplier.toFixed(2))
                });

                // Show winnings display
                this.showWinnings(profit);

                this.showMessage(`🎉 Perfect Game! You won ₦${winnings.toFixed(2)} (Profit: +₦${profit.toFixed(2)})!`, 'win');
                this.updateWalletDisplay();
            }
        }
    }

    async cashOut() {
        if (!this.gameActive || this.gameOver) {
            return;
        }

        const winnings = this.currentStake * this.currentMultiplier;
        const profit = winnings - this.currentStake;
        this.wallet += winnings;
        this.gameActive = false;

        // Log cashout event
        await this.logGameEvent('CASHOUT', {
            amount: parseFloat(winnings.toFixed(2)),
            balance: parseFloat(this.wallet.toFixed(2)),
            multiplier: parseFloat(this.currentMultiplier.toFixed(2))
        });

        // Show winnings display
        this.showWinnings(profit);

        // Play hurray sound
        this.playHurraySound();

        this.showMessage(`💰 Cashed Out! You won ₦${winnings.toFixed(2)} (Profit: +₦${profit.toFixed(2)})!`, 'cashout');
        this.updateWalletDisplay();
    }

    resetGame() {
        console.log('🔄 Resetting game...');

        this.gameActive = false;
        this.gameOver = false;
        this.currentStake = 0;
        this.currentMultiplier = this.config.startingMultiplier;
        this.safeCardsFlipped = 0;
        this.currentSessionId = null;

        this.gameSetup.classList.remove('hidden');
        this.gameInfo.classList.add('hidden');
        this.gameMessageElement.classList.add('hidden');

        // Clear game board
        if (this.gameBoard) {
            this.gameBoard.innerHTML = '';
        }

        // Update stake input max value
        const maxStake = Math.min(this.wallet, this.config.maxStake);
        this.stakeInput.max = maxStake;
        this.stakeInput.value = Math.min(this.stakeInput.value, maxStake);

        console.log('✅ Game reset complete');
    }

    setupGameBoardMonitor() {
        // Monitor when game board gets cleared
        if (this.gameBoard) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && this.gameBoard.children.length === 0 && this.gameActive) {
                        console.error('🚨 ALERT: Game board was cleared while game is active!');
                        console.trace('Game board cleared from:');
                    }
                });
            });

            observer.observe(this.gameBoard, { childList: true });
            console.log('👁️ Game board monitor active');
        }
    }

    async logGameEvent(eventType, eventData = {}) {
        console.log(`🎯 Attempting to log event: ${eventType}`, eventData);

        if (this.offlineMode) {
            console.log(`⚠️ Offline mode - skipping ${eventType} event log`);
            return;
        }

        if (!this.currentSessionId) {
            console.log(`❌ No session ID - skipping ${eventType} event log`);
            return;
        }

        const payload = {
            session_id: this.currentSessionId,
            event_type: eventType,
            ...eventData
        };

        console.log('📤 Sending payload to backend:', payload);

        const response = await this.apiCall('/game/event/', 'POST', payload);

        console.log('📥 Backend response:', response);

        if (!response.success) {
            console.error('❌ Failed to log event:', eventType, response.error);
            // Don't switch to offline mode for individual event failures
        } else {
            console.log('✅ Event logged successfully:', eventType, payload);
        }
    }

    revealAllBombs() {
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                if (this.board[row][col].isBomb && !this.board[row][col].isFlipped) {
                    const cardElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
                    cardElement.classList.add('flipped', 'bomb-revealed');
                    cardElement.textContent = '💣';
                }
            }
        }
    }

    getAllSafeCards() {
        const safeCards = [];
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                if (!this.board[row][col].isBomb) {
                    safeCards.push(this.board[row][col]);
                }
            }
        }
        return safeCards;
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        this.soundToggleBtn.textContent = this.soundEnabled ? '🔊' : '🔇';
        this.soundToggleBtn.classList.toggle('muted', !this.soundEnabled);
        this.soundToggleBtn.title = this.soundEnabled ? 'Mute Sound' : 'Enable Sound';

        // Play a test sound when enabling
        if (this.soundEnabled) {
            this.playDingSound();
        }
    }

    updateGameInfo() {
        this.currentStakeElement.textContent = `₦${this.currentStake.toFixed(2)}`;
        this.currentMultiplierElement.textContent = `${this.currentMultiplier.toFixed(2)}x`;
        this.potentialWinningsElement.textContent = `₦${(this.currentStake * this.currentMultiplier).toFixed(2)}`;
        this.safeCardsElement.textContent = this.safeCardsFlipped;
    }

    updatePlayerInfo() {
        this.currentPlayerElement.textContent = this.userName || 'Guest';
    }

    updateWalletDisplay() {
        this.walletElement.textContent = `₦${this.wallet.toFixed(2)}`;

        // Update stake input max value
        const maxStake = Math.min(this.wallet, this.config.maxStake);
        this.stakeInput.max = maxStake;

        // Disable start button if wallet is empty
        this.startGameBtn.disabled = this.wallet < this.config.minStake;

        if (this.wallet < this.config.minStake) {
            this.showMessage('💸 Wallet empty! Refresh the page to reset your wallet.', 'lose');
        }
    }

    showWinnings(profit) {
        this.lastWinningsElement.textContent = `+₦${profit.toFixed(2)}`;
        this.winningsDisplay.classList.remove('hidden');

        // Auto-hide winnings display after 8 seconds
        setTimeout(() => {
            this.winningsDisplay.classList.add('hidden');
        }, 8000);
    }

    showMessage(text, type) {
        this.gameMessageElement.textContent = text;
        this.gameMessageElement.className = `game-message ${type}`;
        this.gameMessageElement.classList.remove('hidden');

        // Auto-hide message after 5 seconds
        setTimeout(() => {
            this.gameMessageElement.classList.add('hidden');
        }, 5000);
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new BombFlipBettingGame();
});

class GameController {
    constructor() {
        this.musicController = new MusicController();
        this.currentWord = '';
        this.currentIndex = 0;
        this.score = 0;
        this.combo = 0;
        this.accuracy = 100;
        this.gameStartTime = 0;
        this.isPlaying = false;
        this.timingPoints = [];
        this.visualElements = {};
        
        this.initializeEventListeners();
    }

    async initializeGame(level) {
        try {
            // Start music for the level
            await this.musicController.startMusic(level);

            // Get initial challenge
            const challenge = await this.getNextChallenge();
            this.setCurrentWord(challenge.word);

            this.gameStartTime = performance.now();
            this.isPlaying = true;

            // Initialize UI
            this.updateUI();
            this.startGameLoop();

            // Create visualizer if canvas exists
            const canvas = document.getElementById('musicVisualizer');
            if (canvas) {
                this.musicController.createVisualizer(canvas);
            }
        } catch (error) {
            console.error('Error initializing game:', error);
            this.handleGameError('Failed to initialize game');
        }
    }

    initializeEventListeners() {
        // Keyboard input
        document.addEventListener('keydown', this.handleKeyPress.bind(this));

        // Music events
        window.addEventListener('musicStarted', this.onMusicStarted.bind(this));
        window.addEventListener('musicStopped', this.onMusicStopped.bind(this));
        window.addEventListener('musicBeat', this.onMusicBeat.bind(this));
        window.addEventListener('musicError', this.onMusicError.bind(this));

        // Set beat callback
        this.musicController.setBeatCallback(() => {
            this.pulseWordDisplay();
        });
    }

    async getNextChallenge() {
        try {
            const response = await fetch('/api/v1/game/challenge');
            const challenge = await response.json();
            
            if (challenge.error) {
                throw new Error(challenge.error);
            }

            // Sync word with music rhythm
            this.timingPoints = await this.musicController.syncWord(challenge.word);
            return challenge;
        } catch (error) {
            console.error('Error getting challenge:', error);
            this.handleGameError('Failed to get next challenge');
            return null;
        }
    }

    async setCurrentWord(word) {
        this.currentWord = word;
        this.currentIndex = 0;
        
        // Create word display
        const wordDisplay = document.getElementById('wordDisplay');
        wordDisplay.innerHTML = '';
        
        for (let i = 0; i < word.length; i++) {
            const span = document.createElement('span');
            span.textContent = word[i];
            span.className = i === 0 ? 'current' : 'upcoming';
            wordDisplay.appendChild(span);
        }

        // Update timing display
        this.updateTimingDisplay();
    }

    async handleKeyPress(event) {
        if (!this.isPlaying || !this.currentWord) return;

        const expectedChar = this.currentWord[this.currentIndex];
        const pressedChar = event.key;

        if (pressedChar === expectedChar) {
            // Check timing accuracy
            const timing = this.checkTiming();
            this.updateScore(timing);

            // Update display
            this.markCharacterTyped(this.currentIndex, timing);
            this.currentIndex++;

            // Check if word is completed
            if (this.currentIndex >= this.currentWord.length) {
                await this.handleWordCompleted();
            }
        } else {
            this.handleMistake();
        }

        this.updateUI();
    }

    checkTiming() {
        const currentTime = performance.now();
        const expectedTime = this.timingPoints[this.currentIndex];
        const timingDiff = Math.abs(currentTime - expectedTime);
        
        // Convert timing difference to a score (0-1)
        const maxDiff = 200; // Maximum timing difference in ms
        return Math.max(0, 1 - (timingDiff / maxDiff));
    }

    updateScore(timing) {
        const basePoints = 10;
        const comboMultiplier = 1 + (this.combo * 0.1);
        const timingMultiplier = 1 + timing;

        this.score += Math.round(basePoints * comboMultiplier * timingMultiplier);
        this.combo++;
    }

    handleMistake() {
        this.combo = 0;
        this.accuracy = (this.accuracy * (this.currentIndex) + 0) / (this.currentIndex + 1);
        
        // Visual feedback
        const wordDisplay = document.getElementById('wordDisplay');
        const chars = wordDisplay.children;
        chars[this.currentIndex].className = 'mistake';
        
        // Shake effect
        wordDisplay.classList.add('shake');
        setTimeout(() => wordDisplay.classList.remove('shake'), 500);
    }

    async handleWordCompleted() {
        // Submit score
        try {
            const response = await fetch('/api/v1/game/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    word: this.currentWord,
                    score: this.score,
                    accuracy: this.accuracy,
                    combo: this.combo,
                    timing_points: this.timingPoints
                })
            });

            const result = await response.json();
            if (result.error) {
                throw new Error(result.error);
            }

            // Get next challenge
            const challenge = await this.getNextChallenge();
            if (challenge) {
                this.setCurrentWord(challenge.word);
            } else {
                this.endGame();
            }
        } catch (error) {
            console.error('Error submitting score:', error);
            this.handleGameError('Failed to submit score');
        }
    }

    updateUI() {
        // Update score display
        const scoreDisplay = document.getElementById('scoreDisplay');
        if (scoreDisplay) {
            scoreDisplay.textContent = this.score;
        }

        // Update combo display
        const comboDisplay = document.getElementById('comboDisplay');
        if (comboDisplay) {
            comboDisplay.textContent = this.combo;
        }

        // Update accuracy display
        const accuracyDisplay = document.getElementById('accuracyDisplay');
        if (accuracyDisplay) {
            accuracyDisplay.textContent = `${Math.round(this.accuracy)}%`;
        }
    }

    updateTimingDisplay() {
        const timingDisplay = document.getElementById('timingDisplay');
        if (!timingDisplay) return;

        timingDisplay.innerHTML = '';
        this.timingPoints.forEach((time, index) => {
            const marker = document.createElement('div');
            marker.className = 'timing-marker';
            marker.style.left = `${(time - this.gameStartTime) / 20}px`;
            timingDisplay.appendChild(marker);
        });
    }

    pulseWordDisplay() {
        const wordDisplay = document.getElementById('wordDisplay');
        if (!wordDisplay) return;

        wordDisplay.classList.add('pulse');
        setTimeout(() => wordDisplay.classList.remove('pulse'), 100);
    }

    markCharacterTyped(index, timing) {
        const wordDisplay = document.getElementById('wordDisplay');
        const chars = wordDisplay.children;
        
        // Mark current character as typed
        chars[index].className = this.getTimingClass(timing);
        
        // Update next character
        if (index + 1 < chars.length) {
            chars[index + 1].className = 'current';
        }
    }

    getTimingClass(timing) {
        if (timing >= 0.9) return 'perfect';
        if (timing >= 0.7) return 'good';
        if (timing >= 0.5) return 'okay';
        return 'bad';
    }

    startGameLoop() {
        const gameLoop = () => {
            if (!this.isPlaying) return;

            // Update timing display
            this.updateTimingDisplay();

            // Continue loop
            requestAnimationFrame(gameLoop);
        };

        gameLoop();
    }

    async endGame() {
        this.isPlaying = false;
        await this.musicController.stopMusic();

        try {
            const response = await fetch('/api/v1/game/end', {
                method: 'POST'
            });
            const result = await response.json();

            // Show end game screen
            this.showGameOver(result.stats);
        } catch (error) {
            console.error('Error ending game:', error);
            this.handleGameError('Failed to end game properly');
        }
    }

    showGameOver(stats) {
        const gameContainer = document.getElementById('gameContainer');
        gameContainer.innerHTML = `
            <div class="game-over">
                <h2>Game Over!</h2>
                <div class="stats">
                    <p>Final Score: ${this.score}</p>
                    <p>Max Combo: ${stats.max_combo}</p>
                    <p>Accuracy: ${Math.round(this.accuracy)}%</p>
                    <p>Words Completed: ${stats.words_completed}</p>
                </div>
                <button onclick="location.reload()">Play Again</button>
            </div>
        `;
    }

    handleGameError(message) {
        console.error('Game error:', message);
        
        // Show error message to user
        const errorDisplay = document.getElementById('errorDisplay');
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.style.display = 'block';
            setTimeout(() => {
                errorDisplay.style.display = 'none';
            }, 3000);
        }
    }

    // Music event handlers
    onMusicStarted(event) {
        console.log('Music started:', event.detail);
        // Additional initialization if needed
    }

    onMusicStopped() {
        console.log('Music stopped');
        // Cleanup if needed
    }

    onMusicBeat(event) {
        // Visual feedback for beat
        this.pulseWordDisplay();
    }

    onMusicError(event) {
        this.handleGameError(event.detail.error);
    }
}

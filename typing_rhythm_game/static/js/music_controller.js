class MusicController {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.audioElement = null;
        this.currentLevel = null;
        this.isPlaying = false;
        this.startTime = 0;
        this.rhythmPattern = [];
        this.bpm = 120;
    }

    async startMusic(level) {
        try {
            // Stop any existing music
            await this.stopMusic();

            // Get track information
            const response = await fetch(`/music/start/${level}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get track information');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to start music');
            }

            // Create new audio element
            this.audioElement = new Audio(`/music/stream/${level}`);
            this.audioElement.crossOrigin = 'anonymous';

            // Connect to audio context for precise timing
            const source = this.audioContext.createMediaElementSource(this.audioElement);
            source.connect(this.audioContext.destination);

            // Set up rhythm information
            this.bpm = data.rhythm.bpm;
            this.rhythmPattern = data.rhythm.pattern;
            this.currentLevel = level;

            // Start playback
            this.startTime = this.audioContext.currentTime;
            await this.audioElement.play();
            this.isPlaying = true;

            return true;
        } catch (error) {
            console.error('Error starting music:', error);
            return false;
        }
    }

    async stopMusic() {
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
            this.audioElement = null;
        }
        this.isPlaying = false;
    }

    getCurrentBeat() {
        if (!this.isPlaying) return null;

        const currentTime = this.audioContext.currentTime - this.startTime;
        const beatsPerSecond = this.bpm / 60;
        const currentBeat = Math.floor(currentTime * beatsPerSecond);

        return {
            beat: currentBeat,
            pattern: this.rhythmPattern[currentBeat % this.rhythmPattern.length]
        };
    }

    getNextBeatTime() {
        if (!this.isPlaying) return null;

        const currentTime = this.audioContext.currentTime - this.startTime;
        const beatsPerSecond = this.bpm / 60;
        const currentBeat = currentTime * beatsPerSecond;
        const nextBeat = Math.ceil(currentBeat);

        return {
            beat: nextBeat,
            time: (nextBeat / beatsPerSecond) + this.startTime
        };
    }

    syncWord(word) {
        if (!this.isPlaying) return null;

        const nextBeat = this.getNextBeatTime();
        if (!nextBeat) return null;

        const letterTimings = [];
        const beatDuration = 60 / this.bpm;
        let currentBeat = nextBeat.beat;

        for (let i = 0; i < word.length; i++) {
            while (!this.rhythmPattern[currentBeat % this.rhythmPattern.length]) {
                currentBeat++;
            }
            letterTimings.push({
                letter: word[i],
                time: (currentBeat * beatDuration) + this.startTime
            });
            currentBeat++;
        }

        return letterTimings;
    }
}

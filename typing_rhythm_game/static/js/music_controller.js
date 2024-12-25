class MusicController {
    constructor() {
        this.audio = null;
        this.currentLevel = null;
        this.isPlaying = false;
        this.timingPoints = [];
        this.beatCallback = null;
        this.nextBeatTime = 0;
        this.rhythmWorker = null;
        this.initRhythmWorker();
    }

    initRhythmWorker() {
        // Create a worker for precise timing
        const workerBlob = new Blob([`
            let intervalId = null;
            
            self.onmessage = function(e) {
                if (e.data.command === 'start') {
                    intervalId = setInterval(() => {
                        self.postMessage({ type: 'beat' });
                    }, e.data.interval);
                } else if (e.data.command === 'stop') {
                    if (intervalId) {
                        clearInterval(intervalId);
                        intervalId = null;
                    }
                }
            };
        `], { type: 'application/javascript' });

        this.rhythmWorker = new Worker(URL.createObjectURL(workerBlob));
        this.rhythmWorker.onmessage = (e) => {
            if (e.data.type === 'beat') {
                this.onBeat();
            }
        };
    }

    async startMusic(level) {
        try {
            // Stop any existing music
            await this.stopMusic();

            // Start new music
            const response = await fetch(`/api/v1/music/start/${level}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Failed to start music');
            }

            // Create and configure audio
            this.audio = new Audio(`/api/v1/music/stream/${level}`);
            this.audio.addEventListener('canplaythrough', () => {
                this.audio.play();
                this.isPlaying = true;
                this.currentLevel = level;

                // Start rhythm tracking
                const bpm = result.rhythm.bpm;
                const beatInterval = (60 / bpm) * 1000; // Convert to milliseconds
                this.rhythmWorker.postMessage({
                    command: 'start',
                    interval: beatInterval
                });

                // Dispatch event
                window.dispatchEvent(new CustomEvent('musicStarted', {
                    detail: { level, bpm }
                }));
            });

            this.audio.addEventListener('error', (e) => {
                console.error('Audio error:', e);
                this.handleMusicError('Audio playback error');
            });

            return result;
        } catch (error) {
            this.handleMusicError(error);
            throw error;
        }
    }

    async stopMusic() {
        if (this.audio) {
            this.audio.pause();
            this.audio.currentTime = 0;
            this.audio = null;
        }

        this.isPlaying = false;
        this.currentLevel = null;
        this.timingPoints = [];
        this.rhythmWorker.postMessage({ command: 'stop' });

        try {
            await fetch('/api/v1/music/stop', {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error stopping music:', error);
        }

        // Dispatch event
        window.dispatchEvent(new CustomEvent('musicStopped'));
    }

    async syncWord(word) {
        try {
            const response = await fetch('/api/v1/music/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ word })
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Failed to sync word');
            }

            this.timingPoints = result.timing_points;
            return this.timingPoints;
        } catch (error) {
            console.error('Error syncing word:', error);
            return Array(word.length).fill(0); // Fallback timing
        }
    }

    async getCurrentTiming() {
        try {
            const response = await fetch('/api/v1/music/timing');
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.nextBeatTime = result.next_beat;
            return result;
        } catch (error) {
            console.error('Error getting timing:', error);
            return null;
        }
    }

    onBeat() {
        if (this.beatCallback) {
            this.beatCallback();
        }

        // Dispatch beat event
        window.dispatchEvent(new CustomEvent('musicBeat', {
            detail: {
                time: performance.now(),
                level: this.currentLevel
            }
        }));
    }

    setBeatCallback(callback) {
        this.beatCallback = callback;
    }

    handleMusicError(error) {
        console.error('Music error:', error);
        this.stopMusic();
        
        // Dispatch error event
        window.dispatchEvent(new CustomEvent('musicError', {
            detail: { error: error.toString() }
        }));
    }

    // Visual effects methods
    createVisualizer(canvas) {
        if (!this.audio) return;

        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaElementSource(this.audio);
        const analyzer = audioContext.createAnalyser();

        source.connect(analyzer);
        analyzer.connect(audioContext.destination);

        analyzer.fftSize = 256;
        const bufferLength = analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const ctx = canvas.getContext('2d');
        const draw = () => {
            const WIDTH = canvas.width;
            const HEIGHT = canvas.height;

            requestAnimationFrame(draw);

            analyzer.getByteFrequencyData(dataArray);

            ctx.fillStyle = 'rgb(0, 0, 0)';
            ctx.fillRect(0, 0, WIDTH, HEIGHT);

            const barWidth = (WIDTH / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = dataArray[i] / 2;

                const r = barHeight + (25 * (i / bufferLength));
                const g = 250 * (i / bufferLength);
                const b = 50;

                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

                x += barWidth + 1;
            }
        };

        draw();
    }
}

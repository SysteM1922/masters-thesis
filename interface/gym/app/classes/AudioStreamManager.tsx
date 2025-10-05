const DELAY = 500; // Delay em milissegundos antes de iniciar a reprodução

class AudioStreamManager {
    private audioContext: AudioContext | null = null;
    private currentSource: AudioBufferSourceNode | null = null;
    private audioQueue: ArrayBuffer[] = [];
    private isPlaying: boolean = false;
    private playbackTimeout: NodeJS.Timeout | null = null;
    private streamDestination: MediaStreamAudioDestinationNode | null = null;

    public onAudioStart?: () => void;
    public onAudioEnd?: () => void;
    public onAudioStop?: () => void;

    constructor() {
        if (typeof window !== "undefined") {
            this.audioContext = new (window.AudioContext)();
            this.streamDestination = this.audioContext.createMediaStreamDestination();
        }
    }

    public stopCurrentAudio() {
        const wasPlaying = this.isPlaying;

        if (this.playbackTimeout) {
            clearTimeout(this.playbackTimeout);
            this.playbackTimeout = null;
        }

        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch {
                // Ignora erro se já estava parado
            }
            this.currentSource.disconnect();
            this.currentSource = null;
        }

        this.isPlaying = false;

        if (wasPlaying && this.onAudioStop) {
            this.onAudioStop();
        }
    }

    addAudioChunk(audioData: ArrayBuffer) {
        this.audioQueue.push(audioData);

        if (!this.isPlaying && !this.playbackTimeout) {
            this.playbackTimeout = setTimeout(() => {
                this.playAudioQueue();
            }, DELAY);
        }
    }

    private async playAudioQueue() {
        if (!this.audioContext || this.audioQueue.length === 0) {
            return;
        }

        this.isPlaying = true;
        this.playbackTimeout = null;

        try {
            const combinedBuffer = this.combineAudioBuffers(this.audioQueue);
            this.audioQueue = [];

            const audioBuffer = await this.audioContext.decodeAudioData(combinedBuffer);

            this.currentSource = this.audioContext.createBufferSource();
            this.currentSource.buffer = audioBuffer;
            this.currentSource.connect(this.audioContext.destination);

            if (this.streamDestination) {
                this.currentSource.connect(this.streamDestination);
            }

            this.currentSource.onended = () => {
                this.isPlaying = false;
                this.currentSource = null;

                if (this.audioQueue.length > 0) {
                    this.playAudioQueue();
                } else {
                    if (this.onAudioEnd) this.onAudioEnd();
                }
            };

            this.currentSource.start(0);

            if (this.onAudioStart) this.onAudioStart();

        } catch (error) {
            console.error('Erro ao reproduzir áudio:', error);
            this.isPlaying = false;
        }
    }

    private combineAudioBuffers(buffers: ArrayBuffer[]): ArrayBuffer {
        const totalLength = buffers.reduce((acc, buf) => acc + buf.byteLength, 0);
        const combined = new Uint8Array(totalLength);

        let offset = 0;
        for (const buffer of buffers) {
            combined.set(new Uint8Array(buffer), offset);
            offset += buffer.byteLength;
        }

        return combined.buffer;
    }

    public getAudioContext() {
        return this.audioContext;
    }

    public getOutputStream(): MediaStream | null {
        return this.streamDestination ? this.streamDestination.stream : null;
    }

    cleanup() {
        this.stopCurrentAudio();
        this.audioQueue = [];
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

export default AudioStreamManager;
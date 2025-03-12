const serverConfig = {
    host: 'localhost',
    port: 9999
};

const video = document.getElementById('video');

let pc = null;
let dataChannel = null;
let localStream = null;
let signaling = null;
let frameCount = 0;

class WebSocketSignaling {
    constructor(host, port) {
        this.url = `ws://${host}:${port}`;
        this.ws = null;
        this.onmessage = null;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                updateStatus('Connected to server');
                resolve();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (this.onmessage) {
                    this.onmessage(data);
                }
            };

            this.ws.onerror = (error) => {
                updateStatus('Failed to connect to server');
                reject(error);
            };

            this.ws.onclose = () => {
                updateStatus('Disconnected from server');
            };
        });
    }

    async send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    async close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

async function setupPeerConnection() {
    pc = new RTCPeerConnection();

    if (localStream) {
        localStream.getTracks().forEach(track => {
            pc.addTrack(track, localStream);
        });
    }

    dataChannel = pc.createDataChannel('data');
    setupDataChannel();

    pc.onconnectionstatechange = (event) => {
        if (pc.connectionState === 'connected') {
            updateStatus('WebRTC connected');
        } else if (pc.connectionState === 'disconnected') {
            updateStatus('WebRTC disconnected');
        }
    };

    return pc;
}

function setupDataChannel() {
    dataChannel.onopen = () => {
        updateStatus('Data channel is open');
    };

    dataChannel.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'frame') {
            const frame = new Uint8Array(data.frame);
            const blob = new Blob([frame], { type: 'image/jpeg' });
            const url = URL.createObjectURL(blob);
            video.src = url;
            frameCount++;
        }
    };
}

async function startVideoCapture() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video : {
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false,
        });

        video.srcObject = localStream;
        
        return true;
    } catch (error) {
        updateStatus('Error starting video capture: ' + error);
        return false;
    }
}

async function stopConnection() {
    try {
        if (localStream) {
            localStream.getTracks().forEach(track => {
                track.stop();
            });
            localStream = null;
        }

        if (dataChannel) {
            dataChannel.close();
            dataChannel = null;
        }

        if (pc) {
            pc.close();
            pc = null;
        }

        if (signaling) {
            await signaling.close();
            signaling = null;
        }

        video.srcObject = null;

        updateStatus('Connection stopped');
    } catch (error) {
        updateStatus('Error stopping connection: ' + error);
    }
}

window.onload = async () => {
    signaling = new WebSocketSignaling(serverConfig.host, serverConfig.port);
    await signaling.connect();

    await startVideoCapture();
    await setupPeerConnection();
}
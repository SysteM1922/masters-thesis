import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { WebSocketSignalingClient } from './websocket.js'

createApp(App)

const VITE_SIGNALING_SERVER_HOST = import.meta.env.VITE_SIGNALING_SERVER_HOST || '';
const VITE_SIGNALING_SERVER_PORT = import.meta.env.VITE_SIGNALING_SERVER_PORT || '';

let signaling = null;

const pc_config = {
    iceServers: [
        {
            urls: "stun:192.168.1.100:3478",
            username: "gymuser",
            credential: "gym456"
        },
        {
            urls: "turn:192.168.1.100:3478",
            username: "gymuser",
            credential: "gym456"
        },
        {
            urls: "stun:stun.l.google.com:19302"
        }
    ]
};

let pc = new RTCPeerConnection(pc_config);
let stream = null;

const webcamDisplay = document.getElementById('webcamDisplay');
const callButton = document.getElementById('callButton');
const hangupButton = document.getElementById('hangupButton');

//const outputCanvas = document.getElementById('output_canvas');
//const outputCanvasCtx = outputCanvas.getContext('2d');
//const drawingUtils = new DrawingUtils(outputCanvasCtx);

async function startCapture() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { width: 3840, height: 2160 }, audio: false });
        if (!stream) {
            throw new Error('No media stream available');
        }
        webcamDisplay.srcObject = stream;
        webcamDisplay.play();

        stream.getTracks().forEach((track) => {
            console.log('Adding track to peer connection:', track);
            pc.addTrack(track, stream);
        });
        
    } catch (error) {
        console.error('Error accessing media devices.', error);
        alert('Error accessing media devices: ' + error.message);
        return;
    }

    function createTest(dataChannel) {
        console.log('Creating test...');
    }

    try {
        signaling = new WebSocketSignalingClient(
            VITE_SIGNALING_SERVER_HOST,
            VITE_SIGNALING_SERVER_PORT,
            'client1'
        );

        await signaling.connect();

        const dataChannel = pc.createDataChannel('data');

        dataChannel.onopen = () => {
            console.log('Data channel is open');
            createTest(dataChannel);
        };

        dataChannel.onmessage = (event) => {
            console.log('Received message:', event.data);
        };

        pc.onconnectionstatechange = () => {
            console.log('Connection state changed:', pc.connectionState);
            if (pc.connectionState === 'connected') {
                console.log('WebRTC connected');
            } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                console.log('WebRTC connection closed or failed');
                stopCapture();
            }
        };

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('New ICE candidate:', event.candidate);
                signaling.sendIceCandidate(event.candidate);
            }
        }

        pc.oniceconnectionstatechange = () => {
            console.log('ICE connection state changed:', pc.iceConnectionState);
        };

        signaling.handleMessages(pc);

    } catch (error) {
        console.error('Error starting signaling client:', error);
        alert('Error starting signaling client: ' + error.message);
        return;
    }
}

async function stopCapture() {
    if (stream) {
        stream.getTracks().forEach((track) => {
            track.stop();
        });
        stream = null;
    }
    webcamDisplay.srcObject = null;
}


callButton.onclick = async () => {
    console.log('Starting capture...');
    startCapture();
}

hangupButton.onclick = async () => {
    stopCapture();
}
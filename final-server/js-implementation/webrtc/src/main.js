import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { WebSocketSignalingClient } from './websocket.js'
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision'

createApp(App)

const VITE_SIGNALING_SERVER_HOST = import.meta.env.VITE_SIGNALING_SERVER_HOST || '';
const VITE_SIGNALING_SERVER_PORT = import.meta.env.VITE_SIGNALING_SERVER_PORT || '';

let signaling = null;

const pc_config = {
    iceServers: [
        {
            urls: "stun:stun.l.google.com:19302"
        }
    ],
    bundlePolicy: "max-bundle",
    rtcpMuxPolicy: "require",
};

let pc = new RTCPeerConnection(pc_config);
let displayStream = null;

const webcamDisplay = document.getElementById('webcamDisplay');
const callButton = document.getElementById('callButton');
const hangupButton = document.getElementById('hangupButton');

const outputCanvas = document.getElementById('output_canvas');
const outputCanvasCtx = outputCanvas.getContext('2d');
outputCanvas.style.transform = 'scaleX(-1)'; // Mirror the canvas to match the webcam display

const offscreenCanvas = document.createElement('canvas');
const offscreenCanvasCtx = offscreenCanvas.getContext('2d');
const drawingUtils = new DrawingUtils(offscreenCanvasCtx);

function resizeCanvas() {
    const width = webcamDisplay.clientWidth;
    const height = webcamDisplay.clientHeight;
    outputCanvas.width = width;
    outputCanvas.height = height;
    offscreenCanvas.width = width;
    offscreenCanvas.height = height;
    outputCanvasCtx.clearRect(0, 0, width, height);
    offscreenCanvasCtx.clearRect(0, 0, width, height);
}

async function startCapture() {
    try {
        const constraints = {
            video: {
                width: { ideal: 3840 },
                height: { ideal: 2160 },
                frameRate: { ideal: 30 }
            },
            audio: false
        };
        displayStream = await navigator.mediaDevices.getUserMedia(constraints);
        if (!displayStream) {
            throw new Error('No media stream available');
        }
        webcamDisplay.srcObject = displayStream;
        webcamDisplay.style.transform = 'scaleX(-1)';
        webcamDisplay.play();

        const videoTrack = displayStream.getVideoTracks()[0];

        if (!videoTrack) {
            throw new Error('No video track found in the media stream');
        }

        pc.addTrack(videoTrack, displayStream);
        console.log('Added video track to peer connection:', videoTrack);

        resizeCanvas();

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
            offscreenCanvasCtx.clearRect(0, 0, offscreenCanvas.width, offscreenCanvas.height);
            const data = JSON.parse(event.data);

            const landmarks = data.landmarks;
            if (landmarks && landmarks.length > 0) {
                drawingUtils.drawLandmarks(landmarks, { radius: 5, lineWidth: 2, color: '#FFFFFF' });
                drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS, { lineWidth: 2, color: '#FFFFFF' });
            }

            outputCanvasCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
            outputCanvasCtx.drawImage(offscreenCanvas, 0, 0);
        };

        pc.onconnectionstatechange = async () => {
            console.log('Connection state changed:', pc.connectionState);
            if (pc.connectionState === 'connected') {
                console.log('WebRTC connected');

                const sender = pc.getSenders().find(s => s.track.kind === 'video');
                const parameters = sender.getParameters();
                if (sender) {
                    parameters.encodings[0].scaleResolutionDownBy = displayStream.getVideoTracks()[0].getSettings().height / 480;
                    await sender.setParameters(parameters);
                    console.log('Set max bitrate for video sender:', sender.getParameters());
                }

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
    if (displayStream) {
        displayStream.getTracks().forEach((track) => {
            track.stop();
        });
        displayStream = null;
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
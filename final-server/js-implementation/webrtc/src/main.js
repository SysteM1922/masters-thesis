import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

import firebase from 'firebase/compat/app'
import 'firebase/compat/firestore'

const firebaseConfig = {
    apiKey: "AIzaSyDk8wyFzY-_0EfONiMFfjdKkA4OJNCRHCw",
    authDomain: "signaling-server-fca29.firebaseapp.com",
    projectId: "signaling-server-fca29",
    storageBucket: "signaling-server-fca29.firebasestorage.app",
    messagingSenderId: "842750385526",
    appId: "1:842750385526:web:ab172d6793f4c1b91f2e57",
    measurementId: "G-0FYPXNT30G"
};

if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const firestore = firebase.firestore();

createApp(App).mount('#app')


const servers = {
    iceServers: [
        {
            urls: ['stun:stun1.l.google.com:19302', 'stun:stun2.l.google.com:19302'],
        },
    ],
    iceCandidatePoolSize: 10,
};

let pc = new RTCPeerConnection(servers);
let localStream = null;

let dataChannel = null;
let remoteStream = null;
let lastReceivedLandmarks = null;

const webcamVideo = document.getElementById('localVideo');
const callButton = document.getElementById('callButton');
const answerButton = document.getElementById('answerButton');
const hangupButton = document.getElementById('hangupButton');
const callInput = document.getElementById('callInput');

const outputCanvas = document.getElementById('output_canvas');
const outputCanvasCtx = outputCanvas.getContext('2d');
const drawingUtils = new DrawingUtils(outputCanvasCtx);

async function startCapture() {

    await navigator.mediaDevices.getUserMedia({ video: true });
    localStream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
    remoteStream = new MediaStream();

    // Push tracks from local stream to peer connection
    localStream.getTracks().forEach((track) => {
        pc.addTrack(track, localStream);
    });

    webcamVideo.srcObject = localStream;
}

startCapture();

callButton.onclick = async () => {
    webcamVideo.srcObject = remoteStream;
    localStream = null;

    // Pull tracks from remote stream, add to video stream
    pc.ontrack = (event) => {
        event.streams[0].getTracks().forEach((track) => {
            remoteStream = track;
            handleTrack();
        });
    };

    const callDoc = firestore.collection('calls').doc();
    const offerCandidates = callDoc.collection('offerCandidates');
    const answerCandidates = callDoc.collection('answerCandidates');

    callInput.value = callDoc.id;

    callButton.disabled = true;
    answerButton.disabled = true;

    dataChannel = pc.createDataChannel('dataChannel');
    setupDataChannel(dataChannel);

    pc.onicecandidate = (event) => {
        event.candidate && offerCandidates.add(event.candidate.toJSON());
    }

    const offerDescription = await pc.createOffer();
    await pc.setLocalDescription(offerDescription);

    const offer = {
        sdp: offerDescription.sdp,
        type: offerDescription.type,
    };

    await callDoc.set({ offer });

    callDoc.onSnapshot((snapshot) => {
        const data = snapshot.data();
        if (!pc.currentRemoteDescription && data?.answer) {
            const answerDescription = new RTCSessionDescription(data.answer);
            pc.setRemoteDescription(answerDescription);
        }
    });

    answerCandidates.onSnapshot((snapshot) => {
        snapshot.docChanges().forEach((change) => {
            if (change.type === 'added') {
                const candidate = new RTCIceCandidate(change.doc.data());
                pc.addIceCandidate(candidate);
            }
        });
    });
}

answerButton.onclick = async () => {
    webcamVideo.srcObject = localStream;
    
    const callId = callInput.value;
    const callDoc = firestore.collection('calls').doc(callId);
    const answerCandidates = callDoc.collection('answerCandidates');
    const offerCandidates = callDoc.collection('offerCandidates');

    callButton.disabled = true;
    answerButton.disabled = true;

    pc.onicecandidate = (event) => {
        event.candidate && answerCandidates.add(event.candidate.toJSON());
    }

    pc.ondatachannel = (event) => {
        dataChannel = event.channel;
        setupDataChannel(dataChannel);
    }

    const callData = (await callDoc.get()).data();

    const offerDescription = callData.offer;
    await pc.setRemoteDescription(new RTCSessionDescription(offerDescription));

    const answerDescription = await pc.createAnswer();
    await pc.setLocalDescription(answerDescription);

    const answer = {
        type: answerDescription.type,
        sdp: answerDescription.sdp,
    };

    await callDoc.update({ answer });

    offerCandidates.onSnapshot((snapshot) => {
        snapshot.docChanges().forEach((change) => {
            if (change.type === 'added') {
                let data = change.doc.data();
                pc.addIceCandidate(new RTCIceCandidate(data));
            }
        });
    });

    requestAnimationFrame(renderFrame);
}

hangupButton.onclick = async () => {
    pc.close();
    remoteStream.getTracks().forEach((track) => track.stop());
    hangupButton.disabled = true;
    callButton.disabled = false;
    answerButton.disabled = false;
}

function setupDataChannel(channel) {
    channel.onopen = () => {
        console.log('Data channel is open');
    };

    channel.onclose = () => {
        console.log('Data channel is closed');
    };

    channel.onmessage = (event) => {
        console.log('Message received');
        const message = JSON.parse(event.data);
        lastReceivedLandmarks = message;
    };
}


// Pose Estimation
import { Pose } from '@mediapipe/pose';

const pose = new Pose({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
    }
});

pose.setOptions({
    upperBodyOnly: false,
    smoothLandmarks: true,
    modelComplexity: 0,
    gpu: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});

pose.onResults((results) => {
    console.log("Sending pose data");
    dataChannel.send(JSON.stringify(results.poseLandmarks));
});

async function handleTrack() {
    if (!remoteStream) {
        console.error('Remote stream is not available');
        return;
    }
    
    let stream;
    
    // Handle both cases: remoteStream is a MediaStream or a MediaStreamTrack
    if (remoteStream instanceof MediaStreamTrack) {
        stream = new MediaStream([remoteStream]);
    } else if (remoteStream.getTracks) {
        stream = remoteStream;
    } else {
        console.error('Remote stream is neither a MediaStream nor a MediaStreamTrack');
        return;
    }
    
    // Create a video element to process frames
    const video = document.createElement('video');
    video.srcObject = stream;
    video.autoplay = true;
    
    // Wait for video to be ready
    await new Promise(resolve => {
        video.onloadedmetadata = () => {
            resolve();
        };
    });
    
    video.play();
    
    // Function to process frames
    const processFrame = async () => {
        try {
            if (video.paused || video.ended) return;
            
            await pose.send({image: video});
            
            // Request the next frame
            requestAnimationFrame(processFrame);
        } catch (error) {
            console.error('Error processing frame:', error);
            // Continue processing despite errors
            requestAnimationFrame(processFrame);
        }
    };
    
    // Start processing frames
    processFrame();
}


// Display Results
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision';

async function displayResults(results) {
    outputCanvasCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
    outputCanvasCtx.drawImage(webcamVideo, 0, 0, outputCanvas.width, outputCanvas.height);

    if (results) {
        const landmarks = results;
        drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS);
        drawingUtils.drawLandmarks(landmarks);
    }
}

async function renderFrame() {
    // Render the latest landmarks we have
    displayResults(lastReceivedLandmarks);
    // Request next frame (creates continuous loop)
    requestAnimationFrame(renderFrame);
}
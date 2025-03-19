import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { Camera } from '@mediapipe/camera_utils';
import { Pose } from '@mediapipe/pose';
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision';

createApp(App).mount('#app')

const webcamElement = document.getElementById('webcam');
const outputCanvas = document.getElementById('output_canvas');
const outputCanvasCtx = outputCanvas.getContext('2d');
const drawingUtils = new DrawingUtils(outputCanvasCtx);

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
    outputCanvasCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
    outputCanvasCtx.drawImage(
        results.image, 0, 0, outputCanvas.width, outputCanvas.height
    );

    if (results.poseLandmarks) {
        const landmarks = results.poseLandmarks;
        drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS);
        drawingUtils.drawLandmarks(landmarks);
    }
});

const camera = new Camera(webcamElement, {
    onFrame: async () => {
        await pose.send({ image: webcamElement });
    },
    width: 1280,
    height: 720
});
camera.start();
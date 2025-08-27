"use client"

import { useEffect } from 'react';
import { WebSocketSignalingClient } from '../utils/websocket'
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision'

const SIGNALING_SERVER_HOST: string = process.env.SIGNALING_SERVER_HOST ?? "";
const SIGNALING_SERVER_PORT: number = parseInt(process.env.SIGNALING_SERVER_PORT ?? "0");

const pc_config: RTCConfiguration = {
    iceServers: [
        {
            urls: "stun:stun.l.google.com:19302"
        }
    ],
    bundlePolicy: "max-bundle" as RTCBundlePolicy,
    rtcpMuxPolicy: "require" as RTCRtcpMuxPolicy
};

export default function SingleVideo() {

    let signaling: WebSocketSignalingClient;

    let pc: RTCPeerConnection;

    let displayStream: MediaStream | null;

    let webCamDisplay: HTMLVideoElement | null = null;
    let outputCanvas: HTMLCanvasElement;
    let outputCanvasCtx: CanvasRenderingContext2D;

    let offScreenCanvas: HTMLCanvasElement;
    let offScreenCanvasCtx: CanvasRenderingContext2D;

    let topCanvas: HTMLCanvasElement | null = null;
    let topCanvasCtx: CanvasRenderingContext2D | null = null;

    let offScreenTopCanvas: HTMLCanvasElement | null = null;
    let offScreenTopCanvasCtx: CanvasRenderingContext2D | null = null;

    let bottomCanvas: HTMLCanvasElement | null = null;
    let bottomCanvasCtx: CanvasRenderingContext2D | null = null;

    let offScreenBottomCanvas: HTMLCanvasElement | null = null;
    let offScreenBottomCanvasCtx: CanvasRenderingContext2D | null = null;

    let drawingUtils: DrawingUtils;

    useEffect(() => {
        pc = new RTCPeerConnection(pc_config);

        webCamDisplay = document.getElementById("webCamDisplay") as HTMLVideoElement;
        outputCanvas = document.getElementById("output_canvas") as HTMLCanvasElement;
        outputCanvasCtx = outputCanvas.getContext("2d") as CanvasRenderingContext2D;
        if (!outputCanvasCtx) {
            throw new Error("Could not get 2D context from outputCanvas");
        }

        offScreenCanvas = document.createElement("canvas");
        offScreenCanvasCtx = offScreenCanvas.getContext("2d")!;

        if (!offScreenCanvasCtx) {
            throw new Error("Could not get 2D context from offScreenCanvas");
        }

        drawingUtils = new DrawingUtils(offScreenCanvasCtx);
    }, []);

    const resizeCanvas = () => {
        const width = webCamDisplay!.clientWidth;
        const height = webCamDisplay!.clientHeight;
        outputCanvas.width = width;
        outputCanvas.height = height;
        offScreenCanvas.width = width;
        offScreenCanvas.height = height;
        outputCanvasCtx!.clearRect(0, 0, width, height);
        offScreenCanvasCtx!.clearRect(0, 0, width, height);
    };

    const stopCapture = async () => {
        if (displayStream) {
            displayStream.getTracks().forEach((track) => {
                track.stop();
            });
            displayStream = null;
        }
        webCamDisplay!.srcObject = null;
    }

    const startCapture = async () => {
        try {
            const constrains = {
                video: {
                    width: { ideal: 3840 },
                    height: { ideal: 2160 },
                    frameRate: { ideal: 30 }
                },
                audio: false
            };

            displayStream = await navigator.mediaDevices.getUserMedia(constrains);

            if (!displayStream) {
                throw new Error("Could not get user media");
            }

            webCamDisplay!.srcObject = displayStream;

            webCamDisplay!.addEventListener('loadedmetadata', () => {    
                resizeCanvas();
            });

            webCamDisplay!.play();

            const videoTrack = displayStream.getVideoTracks()[0];

            if (!videoTrack) {
                throw new Error("No video track found");
            }

            pc.addTrack(videoTrack, displayStream);


        } catch (error) {
            console.error("Error accessing media devices.", error);
            return;
        }

        try {
            signaling = new WebSocketSignalingClient(
                SIGNALING_SERVER_HOST,
                SIGNALING_SERVER_PORT,
                "client_id"
            );

            await signaling.connect();

            const dataChannel = pc.createDataChannel("data");

            dataChannel.onopen = () => {
                console.log("Data channel opened");
            };

            dataChannel.onmessage = (event: { data: string; }) => {
                offScreenCanvasCtx!.clearRect(0, 0, offScreenCanvas.width, offScreenCanvas.height);
                const data = JSON.parse(event.data);

                const landmarks = data.landmarks;
                if (landmarks && landmarks.length > 0) {
                    drawingUtils.drawLandmarks(landmarks, { radius: 5, lineWidth: 2, color: '#FFFFFF' });
                    drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS, { lineWidth: 2, color: '#FFFFFF' });
                }

                outputCanvasCtx!.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
                outputCanvasCtx!.drawImage(offScreenCanvas, 0, 0);
            };

            pc.onconnectionstatechange = async () => {
                console.log('Connection state changed:', pc.connectionState);
                if (pc.connectionState === 'connected') {
                    console.log('WebRTC connected');

                    const sender = pc.getSenders().find((s) => s.track !== null && s.track.kind === 'video');
                    const parameters = sender!.getParameters();
                    if (sender) {
                        parameters.encodings[0].scaleResolutionDownBy = displayStream!.getVideoTracks()[0].getSettings().height! / 480;
                        await sender.setParameters(parameters);
                        console.log('Set max bitrate for video sender:', sender.getParameters());
                    }

                } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                    console.log('WebRTC connection closed or failed');
                    stopCapture();
                }
            };

            pc.onicecandidate = (event: { candidate: RTCIceCandidate | null; }) => {
                if (event.candidate) {
                    console.log('New ICE candidate:', event.candidate);
                    signaling!.sendIceCandidate(event.candidate);
                }
            }

            pc.oniceconnectionstatechange = () => {
                console.log('ICE connection state changed:', pc.iceConnectionState);
            };

            signaling.handleMessages(pc);

        } catch (error) {
            console.error("Error starting signaling client:", error);
        }
    };

    return (
        <main className="flex h-screen flex-col items-center justify-center p-5">
            <div className="flex flex-col min-w-full min-h-full gap-5">
                <div className="flex flex-2 w-full justify-center align-center gap-2">
                    <div className="flex-1 align-center">
                        <video id="webCamDisplay" className="object-contain bg-amber-100" style={{ transform: 'scaleX(-1)' }} autoPlay playsInline muted></video>
                        <canvas className="absolute top-0 left-0 pointer-events-none" style={{ transform: 'scaleX(-1)' }} id="output_canvas"></canvas>
                    </div>
                    <div className="flex flex-col w-1/6 h-full gap-2">
                        <canvas id="topCanvas" className="flex-1 bg-black"></canvas>
                        <canvas id="bottomCanvas" className="flex-1 bg-black"></canvas>
                    </div>
                </div>
                <div id="buttons" className="flex justify-center items-center w-full gap-10">
                    <button className="btn btn-soft" id="callButton" onClick={startCapture}>Call</button>
                    <button className="btn btn-soft" id="hangupButton" onClick={stopCapture}>Hang Up</button>
                </div>
            </div>
        </main>
    );
}

"use client"

import { useEffect, useRef, useState } from 'react';
import { WebSocketSignalingClient } from '../utils/websocket'
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision'
import { BrowserRouter, Routes, Route, redirect } from 'react-router-dom';
import { BodyDrawer } from '../utils/bodydrawer';

const SIGNALING_SERVER_HOST: string = process.env.SIGNALING_SERVER_HOST ?? "";
const SIGNALING_SERVER_PORT: number = parseInt(process.env.SIGNALING_SERVER_PORT ?? "0");

const TURN_SERVER_HOST: string = process.env.TURN_SERVER_HOST ?? "";
const TURN_SERVER_PORT: number = parseInt(process.env.TURN_SERVER_PORT ?? "0");
const TURN_SERVER_USERNAME: string = process.env.TURN_SERVER_USERNAME ?? "";
const TURN_SERVER_CREDENTIAL: string = process.env.TURN_SERVER_CREDENTIAL ?? "";

const pc_config: RTCConfiguration = {
    iceServers: [
        {
            urls: `turn:${TURN_SERVER_HOST}:${TURN_SERVER_PORT}`,
            username: TURN_SERVER_USERNAME,
            credential: TURN_SERVER_CREDENTIAL
        }
    ],
    bundlePolicy: "max-bundle" as RTCBundlePolicy,
    rtcpMuxPolicy: "require" as RTCRtcpMuxPolicy
};

export default function SingleWorkout() {

    let signaling: WebSocketSignalingClient;

    let pc: RTCPeerConnection;

    let displayStream: MediaStream | null;

    let webCamDisplay: HTMLVideoElement | null = null;
    let outputCanvas: HTMLCanvasElement;
    let outputCanvasCtx: CanvasRenderingContext2D;

    let offScreenCanvas: HTMLCanvasElement;
    let offScreenCanvasCtx: CanvasRenderingContext2D;

    let drawingUtils: DrawingUtils;
    let bodyDrawer: BodyDrawer;

    let dataChannel: RTCDataChannel | null = null;

    const resizeObserverRef = useRef<ResizeObserver | null>(null);

    let repCounter = 0;

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

            dataChannel = pc.createDataChannel("data");

            dataChannel.onopen = () => {
                console.log("Data channel opened");
            };

            dataChannel.onmessage = (event: { data: string; }) => {
                offScreenCanvasCtx!.clearRect(0, 0, offScreenCanvas.width, offScreenCanvas.height);
                const data = JSON.parse(event.data);

                const landmarks = data.landmarks;
                const style = data.style;
                if (landmarks && landmarks.length > 0) {
                    bodyDrawer.drawFromJson(style, landmarks);
                }

                if (data.new_rep) {
                    repCounter += 1;
                    console.log("New rep:", repCounter);
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
        bodyDrawer = new BodyDrawer(drawingUtils);

        const setupResizeObserver = () => {
            if (webCamDisplay && !resizeObserverRef.current) {
                resizeObserverRef.current = new ResizeObserver((entries) => {
                    for (const entry of entries) {
                        if (entry.target === webCamDisplay) {
                            resizeCanvas();
                        }
                    }
                });
                resizeObserverRef.current.observe(webCamDisplay);
            }
        };

        const handleWindowResize = () => {
            resizeCanvas();
        };

        window.addEventListener("resize", handleWindowResize);
        setupResizeObserver();

        startCapture();

        return () => {
            window.removeEventListener("resize", handleWindowResize);
            if (resizeObserverRef.current) {
                resizeObserverRef.current.disconnect();
                resizeObserverRef.current = null;
            }
        };

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

    const startArmsExercise = () => {
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "arms" }));
        }
    }

    const startLegsExercise = () => {
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "legs" }));
        }
    }

    const startWalkExercise = () => {
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "walk" }));
        }
    }

    function BasePageLayout({ children }: { children: React.ReactNode | null }) {
        return (
            <main className="flex justify-center items-center h-screen flex-col w-full gap-5 p-5">
                <div className="flex justify-center gap-2 relative overflow-hidden">
                    <div className='flex relative w-full h-full justify-center'>
                        <div className='flex relative justify-center'>
                            <video
                                id="webCamDisplay"
                                className="max-w-full max-h-full object-contain"
                                style={{ transform: 'scaleX(-1)' }}
                                autoPlay
                                playsInline
                                muted
                            ></video>
                            <div id="overlay" className="absolute w-full h-full object-contain pointer-events-none">
                                {children}
                            </div>
                            <canvas
                                className="absolute max-w-full max-h-full object-contain pointer-events-none"
                                style={{ transform: 'scaleX(-1)' }}
                                id="output_canvas"
                            ></canvas>
                        </div>
                    </div>
                </div>
                <div id="buttons" className="flex justify-center items-center w-full gap-10 flex-shrink-0">
                    <button className="btn btn-soft" id="startButton" onClick={startArmsExercise}>
                        Start Arms Exercise
                    </button>
                    <button className="btn btn-soft" id="startLegsButton" onClick={startLegsExercise}>
                        Start Legs Exercise
                    </button>
                    <button className="btn btn-soft" id="startWalkButton" onClick={startWalkExercise}>
                        Start Walk Exercise
                    </button>
                    <button className="btn btn-soft" id="reloadButton" onClick={() => window.location.href = '/'}>
                        Reload
                    </button>
                </div>
            </main>
        );
    }

    function ArmsExercise() {
        return (
            <BasePageLayout children={
                <main className='w-full h-full'>
                    <div className="absolute inset-0 grid grid-cols-5 grid-rows-3 gap-1 p-2 pointer-events-none">
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>

                        <div className="bg-black bg-opacity-60 rounded-lg p-3 text-white pointer-events-auto w-full">
                            <div className="w-full flex h-full">
                                <p className="text-[clamp(1rem,8vw,4rem)] font-bold leading-none text-center w-full">{repCounter}/10</p>
                            </div>
                        </div>

                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>

                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                        <div></div>
                    </div>
                </main>
            } />
        )
    }

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<ArmsExercise />} />
                <Route path="/arms" element={<ArmsExercise />} />
            </Routes>
        </BrowserRouter>
    );
}

"use client"

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketSignalingClient } from '../utils/websocket'
import { DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { BodyDrawer } from '../utils/bodydrawer';
import { useRouter } from 'next/navigation';

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
    // Usar refs para evitar re-renders
    const signalingRef = useRef<WebSocketSignalingClient | null>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const displayStreamRef = useRef<MediaStream | null>(null);
    const webCamDisplayRef = useRef<HTMLVideoElement | null>(null);
    const outputCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const outputCanvasCtxRef = useRef<CanvasRenderingContext2D | null>(null);
    const offScreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const offScreenCanvasCtxRef = useRef<CanvasRenderingContext2D | null>(null);
    const drawingUtilsRef = useRef<DrawingUtils | null>(null);
    const bodyDrawerRef = useRef<BodyDrawer | null>(null);
    const dataChannelRef = useRef<RTCDataChannel | null>(null);
    const resizeObserverRef = useRef<ResizeObserver | null>(null);

    const counterRef = useRef(0);
    const [repCounter, setRepCounter] = useState(0);

    const router = useRouter();

    function incrementRepCounter() {
        counterRef.current += 1;
        setRepCounter(counterRef.current);
    }

    const stopCapture = useCallback(async () => {
        if (displayStreamRef.current) {
            displayStreamRef.current.getTracks().forEach((track) => {
                track.stop();
            });
            displayStreamRef.current = null;
        }
        if (webCamDisplayRef.current) {
            webCamDisplayRef.current.srcObject = null;
        }
    }, []);

    const resizeCanvas = useCallback(() => {
        const webCamDisplay = webCamDisplayRef.current;
        const outputCanvas = outputCanvasRef.current;
        const offScreenCanvas = offScreenCanvasRef.current;
        const outputCanvasCtx = outputCanvasCtxRef.current;
        const offScreenCanvasCtx = offScreenCanvasCtxRef.current;

        if (!webCamDisplay || !outputCanvas || !offScreenCanvas || !outputCanvasCtx || !offScreenCanvasCtx) {
            return;
        }

        const width = webCamDisplay.clientWidth;
        const height = webCamDisplay.clientHeight;

        // Verificar se as dimensões são válidas
        if (width > 0 && height > 0) {
            outputCanvas.width = width;
            outputCanvas.height = height;
            offScreenCanvas.width = width;
            offScreenCanvas.height = height;
            outputCanvasCtx.clearRect(0, 0, width, height);
            offScreenCanvasCtx.clearRect(0, 0, width, height);
        }
    }, []);

    const startCapture = useCallback(async () => {
        try {
            const constrains = {
                video: {
                    width: { ideal: 3840 },
                    height: { ideal: 2160 },
                    frameRate: { ideal: 30 }
                },
                audio: false
            };

            const stream = await navigator.mediaDevices.getUserMedia(constrains);

            if (!stream) {
                throw new Error("Could not get user media");
            }

            displayStreamRef.current = stream;

            if (webCamDisplayRef.current) {
                webCamDisplayRef.current.srcObject = stream;

                webCamDisplayRef.current.addEventListener('loadedmetadata', () => {
                    resizeCanvas();
                });

                webCamDisplayRef.current.play();
            }

            const videoTrack = displayStreamRef.current.getVideoTracks()[0];

            if (!videoTrack) {
                throw new Error("No video track found");
            }

            if (pcRef.current) {
                pcRef.current.addTrack(videoTrack, displayStreamRef.current);
            }

        } catch (error) {
            console.error("Error accessing media devices.", error);
            return;
        }

        try {
            signalingRef.current = new WebSocketSignalingClient(
                SIGNALING_SERVER_HOST,
                SIGNALING_SERVER_PORT,
                "client_id"
            );

            await signalingRef.current.connect();

            if (pcRef.current) {
                dataChannelRef.current = pcRef.current.createDataChannel("data");

                dataChannelRef.current.onopen = () => {
                    console.log("Data channel opened");
                };

                dataChannelRef.current.onmessage = (event: { data: string; }) => {
                    const offScreenCanvas = offScreenCanvasRef.current;
                    const offScreenCanvasCtx = offScreenCanvasCtxRef.current;
                    const outputCanvas = outputCanvasRef.current;
                    const outputCanvasCtx = outputCanvasCtxRef.current;
                    const bodyDrawer = bodyDrawerRef.current;

                    if (!offScreenCanvas || !offScreenCanvasCtx || !outputCanvas || !outputCanvasCtx || !bodyDrawer) {
                        return;
                    }

                    // Verificar se o canvas tem dimensões válidas antes de limpar
                    if (offScreenCanvas.width > 0 && offScreenCanvas.height > 0) {
                        offScreenCanvasCtx.clearRect(0, 0, offScreenCanvas.width, offScreenCanvas.height);
                    }

                    const data = JSON.parse(event.data);

                    const landmarks = data.landmarks;
                    const style = data.style;
                    if (landmarks && landmarks.length > 0) {
                        bodyDrawer.drawFromJson(style, landmarks);
                    }

                    if (data.new_rep) {
                        incrementRepCounter();
                    }

                    // Verificar dimensões antes de copiar para o canvas de saída
                    if (outputCanvas.width > 0 && outputCanvas.height > 0 && 
                        offScreenCanvas.width > 0 && offScreenCanvas.height > 0) {
                        outputCanvasCtx.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
                        outputCanvasCtx.drawImage(offScreenCanvas, 0, 0);
                    }
                };
            }

            if (pcRef.current && signalingRef.current) {
                pcRef.current.onconnectionstatechange = async () => {
                    const pc = pcRef.current;
                    if (!pc) return;

                    console.log('Connection state changed:', pc.connectionState);
                    if (pc.connectionState === 'connected') {
                        console.log('WebRTC connected');

                        const sender = pc.getSenders().find((s) => s.track !== null && s.track.kind === 'video');
                        const parameters = sender?.getParameters();
                        if (sender && parameters && displayStreamRef.current) {
                            const videoSettings = displayStreamRef.current.getVideoTracks()[0].getSettings();
                            if (videoSettings.height) {
                                parameters.encodings[0].scaleResolutionDownBy = videoSettings.height / 480;
                                await sender.setParameters(parameters);
                                console.log('Set max bitrate for video sender:', sender.getParameters());
                            }
                        }

                    } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                        console.log('WebRTC connection closed or failed');
                        stopCapture();
                    }
                };

                pcRef.current.onicecandidate = (event: { candidate: RTCIceCandidate | null; }) => {
                    if (event.candidate && signalingRef.current) {
                        console.log('New ICE candidate:', event.candidate);
                        signalingRef.current.sendIceCandidate(event.candidate);
                    }
                }

                pcRef.current.oniceconnectionstatechange = () => {
                    if (pcRef.current) {
                        console.log('ICE connection state changed:', pcRef.current.iceConnectionState);
                    }
                };

                signalingRef.current.handleMessages(pcRef.current);
            }

        } catch (error) {
            console.error("Error starting signaling client:", error);
        }
    }, [incrementRepCounter, resizeCanvas, stopCapture]);

    useEffect(() => {
        pcRef.current = new RTCPeerConnection(pc_config);
        
        if (outputCanvasRef.current) {
            outputCanvasCtxRef.current = outputCanvasRef.current.getContext("2d");
            if (!outputCanvasCtxRef.current) {
                throw new Error("Could not get 2D context from outputCanvas");
            }
        }

        offScreenCanvasRef.current = document.createElement("canvas");
        offScreenCanvasCtxRef.current = offScreenCanvasRef.current.getContext("2d");

        if (!offScreenCanvasCtxRef.current) {
            throw new Error("Could not get 2D context from offScreenCanvas");
        }

        drawingUtilsRef.current = new DrawingUtils(offScreenCanvasCtxRef.current);
        bodyDrawerRef.current = new BodyDrawer(drawingUtilsRef.current);

        const setupResizeObserver = () => {
            const webCamDisplay = webCamDisplayRef.current;
            if (webCamDisplay && !resizeObserverRef.current) {
                resizeObserverRef.current = new ResizeObserver((entries) => {
                    for (const entry of entries) {
                        if (entry.target === webCamDisplay) {
                            // Usar requestAnimationFrame para garantir que o resize acontece no próximo frame
                            requestAnimationFrame(() => {
                                resizeCanvas();
                            });
                        }
                    }
                });
                resizeObserverRef.current.observe(webCamDisplay);
            }
        };

        const handleWindowResize = () => {
            requestAnimationFrame(() => {
                resizeCanvas();
            });
        };

        window.addEventListener("resize", handleWindowResize);
        setupResizeObserver();

        startCapture();

        const interval = setInterval(() => {
            setRepCounter(counterRef.current);
        }, 100);

        return () => {
            window.removeEventListener("resize", handleWindowResize);
            if (resizeObserverRef.current) {
                resizeObserverRef.current.disconnect();
                resizeObserverRef.current = null;
            }
            clearInterval(interval);
        };

    }, [startCapture, resizeCanvas]);

    const startArmsExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "arms" }));
        }
    }, []);

    const startLegsExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "legs" }));
        }
    }, []);

    const startWalkExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "walk" }));
        }
    }, []);

    function BasePageLayout({ children }: { children: React.ReactNode | null }) {
        return (
            <main className="flex justify-center items-center h-screen flex-col w-full gap-5 p-5">
                <div className="flex justify-center gap-2 relative overflow-hidden">
                    <div className='flex relative w-full h-full justify-center'>
                        <div className='flex relative justify-center'>
                            <video
                                ref={webCamDisplayRef}
                                className="max-w-full max-h-full object-contain"
                                style={{ transform: 'scaleX(-1)' }}
                                autoPlay
                                playsInline
                                muted
                            ></video>
                            <div id="overlay" className="absolute w-full h-full object-contain pointer-events-none" style={{ zIndex: 2 }}>
                                {children}
                            </div>
                            <canvas
                                className="absolute max-w-full max-h-full object-contain pointer-events-none"
                                style={{ transform: 'scaleX(-1)', zIndex: 1 }}
                                ref={outputCanvasRef}
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
                    <button className="btn btn-soft" id="reloadButton" onClick={() => router.push('/')}>
                        Reload
                    </button>
                    <button className="btn btn-soft" id="incrementRepButton" onClick={incrementRepCounter}>
                        Increment Rep
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
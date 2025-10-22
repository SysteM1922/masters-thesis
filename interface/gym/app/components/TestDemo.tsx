"use client"

import { useEffect, useRef, useState, useCallback, use } from 'react';
import { WebSocketSignalingClient } from '../classes/websocket'
import { ExerciseType } from '../utils/enums';
import { DrawingUtils } from '@mediapipe/tasks-vision'
import { BodyDrawer } from '../utils/bodydrawer';
import { useVoice } from '../contexts/VoiceContext';

const SIGNALING_SERVER_HOST: string = process.env.SIGNALING_SERVER_HOST ?? "";
const SIGNALING_SERVER_PORT: number = parseInt(process.env.SIGNALING_SERVER_PORT ?? "0");

const pc_config: RTCConfiguration = {
    bundlePolicy: "max-bundle" as RTCBundlePolicy,
    rtcpMuxPolicy: "require" as RTCRtcpMuxPolicy
};

export default function TestDemo() {
    // Usar refs para evitar re-renders
    const signalingRef = useRef<WebSocketSignalingClient | null>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const videoSenderRef = useRef<RTCRtpSender | null>(null);
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

    const { clearNoExecutionsTimeout } = useVoice();

    const [isCapturing, setIsCapturing] = useState(false);

    const [repCounter, setRepCounter] = useState(0);

    const [loading, setLoading] = useState(true);

    const incrementRepCounter = useCallback(() => {
        setRepCounter((prev) => prev + 1);
    }, []);

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

    const startConnection = useCallback(async () => {
        try {
            signalingRef.current = new WebSocketSignalingClient(
                SIGNALING_SERVER_HOST,
                SIGNALING_SERVER_PORT,
                "client_id"
            );

            let tries = 0;
            const maxTries = 5;
            
            while (tries < maxTries) {
                try {
                    await signalingRef.current.connect();
                    console.log(`Connected successfully on attempt ${tries + 1}`);
                    break;
                } catch (error) {
                    tries++;
                    console.error(`Connection attempt ${tries} failed:`, error);
                    
                    if (tries >= maxTries) {
                        console.error('Max connection attempts reached');
                        throw new Error('Failed to connect after maximum attempts');
                    }
                    
                    // Wait 1 second before next attempt
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }

            if (pcRef.current) {
                dataChannelRef.current = pcRef.current.createDataChannel("data");
                dataChannelRef.current.binaryType = "arraybuffer";

                dataChannelRef.current.onopen = () => {
                    setLoading(false);
                    console.log("Data channel opened");
                };

                dataChannelRef.current.onmessage = (event: { data: string; }) => {
                    const offScreenCanvas = offScreenCanvasRef.current;
                    const offScreenCanvasCtx = offScreenCanvasCtxRef.current;
                    const outputCanvas = outputCanvasRef.current;
                    const outputCanvasCtx = outputCanvasCtxRef.current;
                    const bodyDrawer = bodyDrawerRef.current;

                    if (!offScreenCanvas || !offScreenCanvasCtx || !outputCanvas || !outputCanvasCtx || !bodyDrawer) {
                        console.error("Canvas or BodyDrawer not initialized");
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
                            }
                        }

                    } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                        console.log('WebRTC connection closed or failed');
                        setIsCapturing(false);
                        stopCapture();
                        alert('Communication lost. Please refresh the page to restart the session.');
                        window.location.reload();
                    }
                };

                pcRef.current.onicecandidate = (event: { candidate: RTCIceCandidate | null; }) => {
                    if (event.candidate && signalingRef.current) {
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
    }, [stopCapture, incrementRepCounter]);

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
            const stream2 = stream.clone(); // Clonar o stream para usar na exibição e não pausar com a pausa do sender

            if (!stream) {
                throw new Error("Could not get user media");
            }

            displayStreamRef.current = stream2;

            if (webCamDisplayRef.current) {
                webCamDisplayRef.current.srcObject = stream;
                setIsCapturing(true);

                webCamDisplayRef.current.addEventListener('loadedmetadata', () => {
                    resizeCanvas();
                });
            }

            const videoTrack = displayStreamRef.current.getVideoTracks()[0];

            if (!videoTrack) {
                throw new Error("No video track found");
            }

            if (pcRef.current) {
                videoSenderRef.current = pcRef.current.addTrack(videoTrack, displayStreamRef.current);
            }

            await startConnection();

        } catch (error) {
            console.error("Error accessing media devices.", error);
            return;
        }

    }, [resizeCanvas, startConnection]);

    useEffect(() => {
        if (pcRef.current !== null) return;

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
    }, [resizeCanvas, startCapture]);

    useEffect(() => {
        clearNoExecutionsTimeout();
    }, []);

    return (
        <main className="relative w-screen h-screen overflow-hidden">
            <div className='absolute inset-5 flex items-center justify-center gap-5'>
                <div className='relative inline-block'>
                    <video
                        // controls // Enable to record
                        ref={webCamDisplayRef}
                        className="block w-auto h-auto object-contain rounded-4xl scale-x-[-1] max-w-[calc(100vw-40px)] max-h-[calc(100vh-40px)]"
                        autoPlay
                        playsInline
                        muted
                    ></video>
                    {isCapturing && (
                        <div className="absolute inset-0 w-full h-full" style={{ zIndex: 2 }}>
                            <main className='w-full h-full'>
                                <div className="absolute inset-0 grid grid-cols-5 grid-rows-3 gap-1 p-2 pointer-events-none">
                                    <div></div>
                                    <div></div>
                                    <div></div>
                                    <div></div>
                                    {!loading && (
                                        <div className="bg-gray-800/90 rounded-4xl text-white pointer-events-auto w-full border-3 border-cyan-700 font-medium font-sans">
                                            <div className="w-full flex h-full flex-col justify-evenly items-center">
                                                <p className="font-medium leading-none text-center text-[clamp(0.8rem,2vw,1.85rem)]">{ExerciseType.ARMS}</p>
                                                <p className="font-semibold leading-none text-center w-full text-[clamp(0.8rem,4vw,4.5rem)]">{repCounter}</p>
                                            </div>
                                        </div>
                                    )}

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

                            {loading && (
                                <div>
                                    <div className="absolute inset-0 z-50 flex items-center justify-center w-full h-full bg-black opacity-70">
                                    </div>
                                    <div className="absolute inset-0 z-50 flex items-center justify-center">
                                        <div className="flex flex-col items-center">
                                            <p className="mb-4 text-white text-4xl font-extrabold">CONNECTING</p>
                                            <span className="loading loading-dots w-40"></span>
                                        </div>
                                    </div>
                                </div>
                            )}

                        </div>
                    )}
                    <canvas
                        className="absolute inset-0 w-full h-full"
                        style={{ transform: 'scaleX(-1)', zIndex: 1 }}
                        ref={outputCanvasRef}
                    ></canvas>
                    {!loading && (
                        <div className="absolute max-h-full max-w-full bottom-0 left-0 m-5" style={{ zIndex: 3 }}>
                            <div id="buttons" className="flex flex-col justify-center items-center gap-10 flex-shrink-0">
                                <button className="btn btn-soft" id="incrementRepButton" onClick={incrementRepCounter}>
                                    Increment Rep
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </main >
    );
}
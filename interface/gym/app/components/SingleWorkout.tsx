"use client"

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketSignalingClient } from '../classes/websocket'
import { ExerciseType } from '../utils/enums';
import { DrawingUtils } from '@mediapipe/tasks-vision'
import { BodyDrawer } from '../utils/bodydrawer';
import { useVoice } from '../contexts/VoiceContext';
import { redirect } from 'next/navigation';

const SIGNALING_SERVER_HOST: string = process.env.SIGNALING_SERVER_HOST ?? "";
const SIGNALING_SERVER_PORT: number = parseInt(process.env.SIGNALING_SERVER_PORT ?? "0");

const TURN_SERVER_HOST: string = process.env.TURN_SERVER_HOST ?? "";
const TURN_SERVER_PORT: number = parseInt(process.env.TURN_SERVER_PORT ?? "0");
const TURN_SERVER_USERNAME: string = process.env.TURN_SERVER_USERNAME ?? "";
const TURN_SERVER_CREDENTIAL: string = process.env.TURN_SERVER_CREDENTIAL ?? "";

const maxLegReps = 10;
const maxArmReps = 10;
const maxWalkSeconds = 60;

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

    const [showingExerciseModal, setShowingExerciseModal] = useState(false);

    const videoPath = useRef<string>("/exercise1.mp4");

    const [isCapturing, setIsCapturing] = useState(false);

    const [actualExercise, setActualExercise] = useState<ExerciseType>(ExerciseType.ARMS);
    const [repCounter, setRepCounter] = useState(0);

    const [minsTimer, setMinsTimer] = useState(0);
    const [secsTimer, setSecsTimer] = useState(0);

    const [walkSecondsLeft, setWalkSecondsLeft] = useState(maxWalkSeconds);
    const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const [loading, setLoading] = useState(true);

    const { sendMessage, onVoiceCommand, onSpeakingChange, startListening } = useVoice();
    const [confirmation, setConfirmation] = useState(false);

    const [waitingForConfirmation, setWaitingForConfirmation] = useState(false);
    const [waitingForListening, setWaitingForListening] = useState(false);

    const waitingForListeningRef = useRef<boolean>(false);

    useEffect(() => {
        waitingForListeningRef.current = waitingForListening;
    }, [waitingForListening]);

    useEffect(() => {
        const unsubscribe = onSpeakingChange((speaking: boolean) => {
            if (waitingForListeningRef.current && !speaking) {
                startListening();
                setWaitingForListening(false);
            }
        });

        return unsubscribe;
    }, [onSpeakingChange, startListening]);

    useEffect(() => {
        const unsubscribe = onVoiceCommand((command: string) => {
            if (command === "affirm" || command === "start_training_session") {
                setTimeout(() => {
                    setConfirmation(true);
                }, 1000);
            }
            else if (command === "deny") {
                setConfirmation(false);
            }
            else if (command === "next_exercise") {
                if (!waitingForConfirmation) {
                    setWaitingForConfirmation(true);
                    setWaitingForListening(true);
                }
            }
        });

        return () => {
            unsubscribe();
        };
    }, [onVoiceCommand]);

    const incrementRepCounter = () => {
        setRepCounter((prev) => prev + 1);
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

    const startConnection = useCallback(async () => {
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
                    setLoading(false);
                    setTimeout(() => {
                        setShowingExerciseModal(true);
                        sendMessage({ type: "arms_exercise" });
                        setWaitingForListening(true);
                        console.log("Data channel opened");
                    }, 1000);
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
    }, [stopCapture, sendMessage]);

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
                videoSenderRef.current.track!.enabled = false;
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

        return () => {
            window.removeEventListener("resize", handleWindowResize);
            if (resizeObserverRef.current && webCamDisplayRef.current) {
                resizeObserverRef.current.unobserve(webCamDisplayRef.current);
                resizeObserverRef.current.disconnect();
                resizeObserverRef.current = null;
            }
            if (pcRef.current) {
                pcRef.current.close();
                pcRef.current = null;
            }
            if (signalingRef.current) {
                signalingRef.current.close();
                signalingRef.current = null;
            }
            stopCapture();
            setIsCapturing(false);
        };
    }, [resizeCanvas]);

    const clearWalkTimer = useCallback(() => {
        if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
        }
    }, []);

    const startWalkTimer = useCallback(() => {
        clearWalkTimer();

        setWalkSecondsLeft(maxWalkSeconds);

        timerIntervalRef.current = setInterval(() => {
            setWalkSecondsLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timerIntervalRef.current!);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);


    }, [maxWalkSeconds, clearWalkTimer]);

    useEffect(() => {
        if (actualExercise === ExerciseType.WALK && !showingExerciseModal) {
            startWalkTimer();
        } else {
            clearWalkTimer();
        }

        return () => {
            clearWalkTimer();
        };
    }, [actualExercise, showingExerciseModal]);

    useEffect(() => {
        setMinsTimer(Math.floor(walkSecondsLeft / 60));
        setSecsTimer(walkSecondsLeft % 60);
    }, [walkSecondsLeft]);

    const startArmsExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "arms" }));
            setActualExercise(ExerciseType.ARMS);
            setRepCounter(0);
        }
    }, []);

    const startLegsExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            if (actualExercise === ExerciseType.RIGHT_LEG) {
                dataChannel.send(JSON.stringify({ exercise: "legs", right_leg: false }));
                setActualExercise(ExerciseType.LEFT_LEG);
                setRepCounter(0);
            } else {
                dataChannel.send(JSON.stringify({ exercise: "legs", right_leg: true }));
                setActualExercise(ExerciseType.RIGHT_LEG);
                setRepCounter(0);
            }
        }
    }, [actualExercise]);

    const startWalkExercise = useCallback(() => {
        const dataChannel = dataChannelRef.current;
        if (dataChannel && dataChannel.readyState === "open") {
            dataChannel.send(JSON.stringify({ exercise: "walk" }));
            setActualExercise(ExerciseType.WALK);
            setRepCounter(0);
            setWalkSecondsLeft(maxWalkSeconds);
        }
    }, []);

    const pauseStreaming = () => {
        if (videoSenderRef.current) {
            videoSenderRef.current.track!.enabled = false;
        }
    };

    const resumeStreaming = () => {
        if (videoSenderRef.current) {
            videoSenderRef.current.track!.enabled = true;
        }
    };

    useEffect(() => {
        if (confirmation) {
            if (waitingForConfirmation) {
                setWaitingForConfirmation(false);
                if (actualExercise === ExerciseType.ARMS) {
                    pauseStreaming();
                    videoPath.current = "/exercise1.mp4";
                    setTimeout(() => {
                        setShowingExerciseModal(true);
                        startLegsExercise();
                        sendMessage({ type: "legs_exercise" });
                        setWaitingForListening(true);
                    }, 3000);
                }
                else if (actualExercise === ExerciseType.RIGHT_LEG) {
                    sendMessage({ type: "change_legs" });
                    startLegsExercise();
                }
                else if (actualExercise === ExerciseType.LEFT_LEG) {
                    pauseStreaming();
                    videoPath.current = "/exercise1.mp4";
                    setTimeout(() => {
                        setShowingExerciseModal(true);
                        setActualExercise(ExerciseType.WALK);
                        sendMessage({ type: "walk_exercise" });
                        setWaitingForListening(true);
                    }, 3000);
                }
                else if (actualExercise === ExerciseType.WALK) {
                    pauseStreaming();
                    sendMessage({ type: "goodbye" });
                    setTimeout(() => {
                        redirect("/bye");
                    }, 3000);
                }

            } else if (actualExercise === ExerciseType.WALK) {
                startWalkExercise();
            }
            resumeStreaming();
            setShowingExerciseModal(false);
            setConfirmation(false);
        }
    }, [confirmation, actualExercise, startArmsExercise, startLegsExercise, startWalkExercise]);

    useEffect(() => {
        if ((actualExercise === ExerciseType.LEFT_LEG || actualExercise === ExerciseType.RIGHT_LEG) && repCounter >= maxLegReps) {
            if (actualExercise === ExerciseType.RIGHT_LEG) {
                sendMessage({ type: "change_legs" });
                startLegsExercise();
            } else {
                sendMessage({ type: "exercise_done" });
                pauseStreaming();
                videoPath.current = "/exercise1.mp4";
                setTimeout(() => {
                    setShowingExerciseModal(true);
                    setActualExercise(ExerciseType.WALK);
                    sendMessage({ type: "walk_exercise" });
                    setWaitingForListening(true);
                }, 3000);
            }
        }
        else if (actualExercise === ExerciseType.ARMS && repCounter >= maxArmReps) {
            sendMessage({ type: "exercise_done" });
            pauseStreaming();
            videoPath.current = "/exercise1.mp4";
            setTimeout(() => {
                setShowingExerciseModal(true);
                startLegsExercise();
                sendMessage({ type: "legs_exercise" });
                setWaitingForListening(true);
            }, 3000);
        }
        else if (actualExercise === ExerciseType.WALK && walkSecondsLeft <= 0) {
            pauseStreaming();
            sendMessage({ type: "goodbye" });
            setTimeout(() => {
                redirect("/bye");
            }, 5000);
        }
    }, [repCounter, actualExercise, walkSecondsLeft]);

    return (
        <main className="flex justify-center items-center h-screen w-full gap-5 p-15">
            <div id="buttons" className="flex flex-col justify-center items-center gap-10 flex-shrink-0">
                <button className="btn btn-soft" id="startButton" onClick={startArmsExercise}>
                    Start Arms Exercise
                </button>
                <button className="btn btn-soft" id="startLegsButton" onClick={startLegsExercise}>
                    Start Legs Exercise
                </button>
                <button className="btn btn-soft" id="startWalkButton" onClick={startWalkExercise}>
                    Start Walk Exercise
                </button>
                <button className="btn btn-soft" id="incrementRepButton" onClick={incrementRepCounter}>
                    Increment Rep
                </button>
            </div>
            <div className="flex justify-center gap-2 relative overflow-hidden">
                <div className='flex relative w-full h-full justify-center'>
                    <div className='flex relative justify-center'>
                        <video
                            ref={webCamDisplayRef}
                            className="max-w-full max-h-full object-contain rounded-4xl"
                            style={{ transform: 'scaleX(-1)' }}
                            autoPlay
                            playsInline
                            muted
                        ></video>
                        {isCapturing && (
                            <div id="overlay" className="absolute w-full h-full object-contain pointer-events-none" style={{ zIndex: 2 }}>
                                <main className='w-full h-full'>
                                    <div className="absolute inset-0 grid grid-cols-5 grid-rows-3 gap-1 p-2 pointer-events-none">
                                        <div></div>
                                        <div></div>
                                        <div></div>
                                        <div></div>
                                        {!loading && (
                                            <div className="bg-gray-800/90 rounded-4xl text-white pointer-events-auto w-full border-3 border-cyan-700 font-medium font-sans">
                                                {actualExercise === ExerciseType.ARMS && (
                                                    <div className="w-full flex h-full flex-col justify-evenly items-center">
                                                        <p className="font-medium leading-none text-center text-3xl">{ExerciseType.ARMS}</p>
                                                        <p className="font-semibold leading-none text-center w-full text-7xl">{repCounter}/{maxArmReps}</p>
                                                    </div>
                                                )}
                                                {actualExercise === ExerciseType.RIGHT_LEG && (
                                                    <div className="w-full flex h-full flex-col justify-evenly items-center">
                                                        <p className="font-medium leading-none text-center text-3xl">{ExerciseType.RIGHT_LEG}</p>
                                                        <p className="font-semibold leading-none text-center w-full text-7xl">{repCounter}/{maxLegReps}</p>
                                                    </div>
                                                )}
                                                {actualExercise === ExerciseType.LEFT_LEG && (
                                                    <div className="w-full flex h-full flex-col justify-evenly items-center">
                                                        <p className="font-medium leading-none text-center text-3xl">{ExerciseType.LEFT_LEG}</p>
                                                        <p className="font-semibold leading-none text-center w-full text-7xl">{repCounter}/{maxLegReps}</p>
                                                    </div>
                                                )}
                                                {actualExercise === ExerciseType.WALK && (
                                                    <div className="w-full flex h-full flex-col justify-evenly items-center">
                                                        <p className="font-medium leading-none text-center text-3xl">{ExerciseType.WALK}</p>
                                                        <p className="font-bold leading-none text-center w-full text-1.5xl">
                                                            {String(minsTimer).padStart(2, '0')}:{String(secsTimer).padStart(2, '0')}
                                                        </p>
                                                        <p className="font-semibold leading-none text-center w-full text-7xl">{repCounter}</p>
                                                    </div>
                                                )}
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
                                        <div className="absolute inset-0 z-50 flex items-center justify-center w-full h-full bg-black opacity-70 rounded-4xl">
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
                            className="absolute max-w-full max-h-full object-contain pointer-events-none"
                            style={{ transform: 'scaleX(-1)', zIndex: 1 }}
                            ref={outputCanvasRef}
                        ></canvas>
                    </div>
                </div>
            </div>
            {showingExerciseModal && (
                <div className="absolute inset-0 z-50 flex items-center justify-center w-full h-full bg-black bg-opacity-70">
                    <video className="max-w-full max-h-full" muted autoPlay loop>
                        <source src={videoPath.current} type="video/mp4" />
                        Your browser does not support the video tag.
                    </video>
                </div>
            )}
        </main>
    );
}
"use client"

import { useEffect, useState, useRef, useCallback, use } from "react"
import { motion, scale, useAnimation } from "framer-motion";
import { usePorcupine } from "@picovoice/porcupine-react"
import { useColor } from "../contexts/ColorContext";
import { useVoice } from "../contexts/VoiceContext";
import { useLandPage } from "../contexts/LandPageContext";
import { redirect } from "next/navigation";
import AudioStreamManager from "../classes/AudioStreamManager";

const ACCESS_KEY = process.env.PORCUPINE_ACCESS_KEY || "";
const modelFilePath = "/porcupine_params_pt.pv";
const keywordFilePath = "/Ola-Jim_pt_wasm_v3_0_0.ppn";

if (ACCESS_KEY === "") {
    throw new Error("Missing Porcupine AccessKey. Please add it to your environment variables.");
}

export default function VoiceComponent() {

    const { landPageStep, setLandPageStep } = useLandPage();
    const { setTextColor } = useColor();
    const { sendMessage, setWebSocket, notifyVoiceCommand, speaking, setSpeaking, setStartListeningFunction } = useVoice();
    const [listening, setListening] = useState(false);
    const speakingRef = useRef(speaking);
    const [interim, setInterim] = useState("");
    const [finalText, setFinalText] = useState("");
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const shouldSendMessage = useRef(true);
    const landPageStepRef = useRef(landPageStep);
    const managerRef = useRef<AudioStreamManager | null>(null);
    
    const [micStream, setMicStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then((stream) => {
                setMicStream(stream);
            }).catch((err) => {
                console.error("Error accessing microphone:", err);
            });
    }, []);

    useEffect(() => {
        landPageStepRef.current = landPageStep;
    }, [landPageStep]);

    const {
        keywordDetection,
        isLoaded,
        //isListening,
        error,
        init,
        start,
        stop,
        release,
    } = usePorcupine();

    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        speakingRef.current = speaking;
    }, [speaking]);

    useEffect(() => {
        if (ws.current) {
            return;
        }

        managerRef.current = new AudioStreamManager();

        managerRef.current.onAudioStart = () => {
            setSpeaking(true);
        };

        managerRef.current.onAudioEnd = () => {
            setSpeaking(false);
        };

        managerRef.current.onAudioStop = () => {
            setSpeaking(false);
        };

        ws.current = new WebSocket("ws://localhost:8100/ws/session");
        ws.current.binaryType = "arraybuffer";

        setWebSocket(ws.current);

        ws.current!.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "audio") {
                    // Notificar os callbacks quando receber uma intent
                    if (data.intent) {
                        notifyVoiceCommand(data.intent);
                        if (speakingRef.current) {
                            managerRef.current?.stopCurrentAudio();
                        }
                        if (landPageStepRef.current === 4 && (data.intent === "start_training_session")) {
                            setTimeout(() => {
                                setLandPageStep(5);
                            }, 1000);
                        }
                        if (landPageStepRef.current === 5) {
                            if (data.intent === "affirm") {
                                setLandPageStep(6);
                            } else if (data.intent === "deny") {
                                setLandPageStep(4);
                            }
                        }
                    }
                }
            } catch {
                // Not JSON, assume binary audio data
                managerRef.current?.addAudioChunk(event.data);
            }
        };

        ws.current.onopen = () => {
            console.log("WebSocket connection established");
        };

        ws.current.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        ws.current.onclose = () => {
            console.log("WebSocket connection closed");
        };

        return () => {
            ws.current?.close();
        }
    }, []);

    useEffect(() => {

        if (typeof window === 'undefined') {
            return;
        }

        const SpeechRecognitionAPI = (window as Window & typeof globalThis).SpeechRecognition ||
            (window as Window & typeof globalThis).webkitSpeechRecognition;

        if (!SpeechRecognitionAPI) {
            console.error("Speech Recognition API not supported in this browser.");
            return;
        }

        const recognition = new SpeechRecognitionAPI();
        recognitionRef.current = recognition;
        recognition.lang = 'pt-PT';
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.maxAlternatives = 5;

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interimTranscript = "";
            let finalTranscript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const res = event.results[i];
                if (res.isFinal) {
                    finalTranscript += res[0].transcript;
                } else {
                    interimTranscript += res[0].transcript;
                }
            }
            if (finalTranscript) {
                setFinalText((prev: string) => (prev ? prev + " " + finalTranscript : finalTranscript));

                if (shouldSendMessage.current) {
                    sendMessage({ type: "new_command", command: finalTranscript });
                }
                else {
                    setTimeout(() => {
                        setLandPageStep(landPageStepRef.current + 1);
                    }, 1000);
                }
            }
            setInterim(interimTranscript);
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            console.warn("Speech recognition error:", event.error);
        };

        recognition.onend = () => {
            setTimeout(() => {
                setListening(false);
                setTextColor("text-white");
                recognitionRef.current?.stop();
                setInterim("");
                setFinalText("");
            }, 1000);

            return () => {
                recognition.abort();
            }
        };
    }, []);

    useEffect(() => {
        async function initPorcupine() {
            if (!isLoaded) {
                await init(
                    ACCESS_KEY,
                    { publicPath: keywordFilePath, label: "Olá Jim", sensitivity: 0.5 },
                    { publicPath: modelFilePath }
                ).then(
                    async () => {
                        console.log("Porcupine initialized");
                        await start();
                    }
                );
            }
        }
        initPorcupine();

    }, [init, start, isLoaded]);

    // Cleanup no unmount
    useEffect(() => {
        return () => {
            stop();
            release();
        }
    }, [stop, release]);

    const startListening = useCallback(() => {
        if (recognitionRef.current && !listening) {
            try {
                recognitionRef.current.start();
                setListening(true);
                setInterim("");
            } catch (e) {
                console.error("Error starting recognition:", e);
            }
        }
    }, [listening]);

    useEffect(() => {
        setStartListeningFunction(startListening);
    }, [setStartListeningFunction, startListening]);

    useEffect(() => {
        if (window.location.pathname === "/") {
            if (!speaking) {
                if (landPageStep === 0) {
                    sendMessage({ type: "presentation1" });
                    setTimeout(() => {
                        setLandPageStep(1);
                    }, 1000);
                } else if (landPageStep === 5) {
                    startListening();
                }
            }
        }
    }, [speaking]);

    const handleKeywordDetection = useCallback(() => {
        if (window.location.pathname === "/") {
            setTextColor("text-green-600");
            if (landPageStep === -1) {
                sendMessage({ type: "presentation0" });
                setSpeaking(true);
                setLandPageStep(0);
            }
            else if (landPageStep === 1) {
                sendMessage({ type: "presentation2" });
                setTimeout(() => {
                    setLandPageStep(2);
                }, 1000);
            }
            else if (landPageStep === 2) {
                shouldSendMessage.current = false;
                startListening();
            }
            else {
                startListening();
            }
        }
        else {
            startListening();
        }
    }, [sendMessage, setTextColor, startListening, landPageStep, setLandPageStep]);

    useEffect(() => {
        if (landPageStep < 3) {
            setTextColor("text-white");
        }
        if (landPageStep === 3) {
            sendMessage({ type: "presentation3" });
        } else if (landPageStep === 4) {
            if (!shouldSendMessage.current) {
                sendMessage({ type: "presentation4" });
            }
            shouldSendMessage.current = true;
        } else if (landPageStep === 6) {
            sendMessage({ type: "lets_go" });
            setTimeout(() => {
                redirect("/workout");
            }, 1000);
        }
    }, [landPageStep]);

    useEffect(() => {
        if (keywordDetection) {
            handleKeywordDetection();
        }
    }, [keywordDetection]);

    useEffect(() => {
        if (error) {
            console.error(error);
        }
    }, [error]);


    // Animation

    const controls = useAnimation();
    const [outPutLevel, setOutPutLevel] = useState(0);
    const [micLevel, setMicLevel] = useState(0);
    const analyserRef = useRef<AnalyserNode | null>(null);

    const audioContext = managerRef.current?.getAudioContext();
    const outPutStream = managerRef.current?.getOutputStream();

    useEffect(() => {

        if (!audioContext || !outPutStream) return;

        const source = audioContext.createMediaStreamSource(outPutStream);

        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function tick() {
            analyser.getByteFrequencyData(dataArray);
            const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;

            setOutPutLevel(avg / 256); // Normaliza para 0-1

            requestAnimationFrame(tick);
        }

        tick();

        return () => {
            analyser.disconnect();
            source.disconnect();
            analyserRef.current = null;
        };
    }, [outPutStream]);

    useEffect(() => {

        if (!audioContext || !micStream) return;

        const source = audioContext.createMediaStreamSource(micStream);

        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function tick() {
            analyser.getByteFrequencyData(dataArray);
            const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;

            setMicLevel(avg / 256); // Normaliza para 0-1

            requestAnimationFrame(tick);
        }

        tick();

        return () => {
            analyser.disconnect();
            source.disconnect();
            analyserRef.current = null;
            micStream.getTracks().forEach(track => track.stop());
        };
    }, [micStream]);

    useEffect(() => {
        if (speaking) {
            controls.start({
                scale: 1 + 2 * outPutLevel,
                transition: { duration: 0.1, ease: "easeOut" }
            });
        }
        else if (listening) {
            controls.start({
                scale: 1 + 2 * micLevel,
                transition: { duration: 0.1, ease: "easeOut" }
            });
        }
        else {
            controls.start({ scale: 1, transition: { duration: 0.3 } });
        }
    }, [speaking, listening, outPutLevel, micLevel]);

    return (
        <>
            {/*listening && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
                        <div className="text-center">
                            <div className="mb-4">
                                <div className="w-12 h-12 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900">A escutar...</h3>
                            </div>

                            <div className="space-y-3">
                                {interim && (
                                    <div className="p-3 bg-gray-100 rounded-lg">
                                        <p className="text-gray-800 italic">{interim}</p>
                                    </div>
                                )}

                                {finalText && (
                                    <div className="p-3 bg-green-50 rounded-lg">
                                        <p className="text-green-600 font-medium">{finalText}</p>
                                    </div>
                                )}
                            </div>

                            <div className="mt-4">
                                <p className="text-xs text-gray-500">Fale claramente para melhor reconhecimento</p>
                            </div>
                        </div>
                    </div>
                </div>
            )*/}
            <div
                className="fixed bottom-12 right-12 w-14 h-14 rounded-full z-50 flex items-center justify-center opacity-75"
                style={{
                    backgroundColor: speaking
                        ? "rgba(47, 240, 45, 0.8)"
                        : listening
                            ? "rgba(245, 39, 67, 0.8)"
                            : "rgba(16, 89, 231, 0.8)"
                }}
            >
            </div>
            <motion.div
                animate={controls}
                className="fixed bottom-12 right-12 w-14 h-14 rounded-full z-51 flex items-center justify-center shadow-lg opacity-25"
                style={{
                    backgroundColor: speaking
                        ? "rgba(47, 240, 45, 0.8)"
                        : listening
                            ? "rgba(245, 39, 67, 0.8)"
                            : "rgba(16, 89, 231, 0.8)"
                }}
            >
            </motion.div>
        </>
    )
}
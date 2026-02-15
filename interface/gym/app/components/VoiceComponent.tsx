"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { motion, useAnimation } from "framer-motion";
import { useColor } from "../contexts/ColorContext";
import { useVoice } from "../contexts/VoiceContext";
import { useLandPage } from "../contexts/LandPageContext";
import { redirect } from "next/navigation";
import AudioStreamManager from "../classes/AudioStreamManager";

export default function VoiceComponent() {

    const { landPageStep, setLandPageStep } = useLandPage();
    const { setTextColor } = useColor();
    const { sendMessage, setWebSocket, notifyVoiceCommand, speaking, setSpeaking, setStartListeningFunction, resetNoExecutionsTimeout, clearNoExecutionsTimeout } = useVoice();
    const [listening, setListening] = useState(false);
    const speakingRef = useRef(speaking);
    const [interim, setInterim] = useState("");
    const [finalText, setFinalText] = useState("");
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const shouldSendMessage = useRef(true);
    const landPageStepRef = useRef(landPageStep);
    const managerRef = useRef<AudioStreamManager | null>(null);
    const [intent, setIntent] = useState("");
    const lastIntentRef = useRef("");

    const [micStream, setMicStream] = useState<MediaStream | null>(null);

    const [keywordDetection, setKeywordDetection] = useState(false);

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

    const ws = useRef<WebSocket | null>(null);
    const openWakeWordWS = useRef<WebSocket | null>(null);

    useEffect(() => {
        speakingRef.current = speaking;
    }, [speaking]);

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
        resetNoExecutionsTimeout();
    }, [listening]);

    useEffect(() => {
        setStartListeningFunction(startListening);
    }, [setStartListeningFunction, startListening]);

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
                    if (speakingRef.current) {
                        managerRef.current?.stopCurrentAudio();
                    }
                }
                if (data.intent) {
                    notifyVoiceCommand(data.intent);
                    setIntent(data.intent);
                    if (landPageStepRef.current === 4 && (data.intent === "start_training_session" || data.intent === "affirm")) {
                        setTimeout(() => {
                            setLandPageStep(5);
                            sendMessage({ type: "presentation5" });
                        }, 2000);
                    }
                    if (landPageStepRef.current === 5) {
                        if (data.intent === "affirm") {
                            setLandPageStep(6);
                        } else if (data.intent === "deny") {
                            setLandPageStep(4);
                        }
                    }
                }
            } catch {
                // Not JSON, assume binary audio data
                managerRef.current?.addAudioChunk(event.data);
            }
        };

        ws.current.onopen = () => {
            console.log("Gym-Service connection established");
        };

        ws.current.onerror = (error) => {
            console.error("Gym-Service error:", error);
        };

        ws.current.onclose = () => {
            console.log("Gym-Service connection closed");
            // Show an alert to the user and then reload the page
            alert("Gym-Service not running.\nPlease start the Gym-Service and reload the page.");
            window.location.reload();
        };

        return () => {
            ws.current?.close();
        }
    }, []);


    useEffect(() => {
        if (openWakeWordWS.current) {
            return;
        }

        openWakeWordWS.current = new WebSocket("ws://localhost:8100/ws/wakeword");

        openWakeWordWS.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                switch (data.type) {
                    case "wakeword_status":
                        console.log("Wake word detection status:", data.status);
                        break;
                    case "wakeword_detected":
                        console.log("Wake word detected with confidence:", data.confidence);
                        
                        if (speakingRef.current) {
                            console.log("Already speaking, ignoring wake word detection");
                            return;
                        }

                        if (listening) {
                            console.log("Already listening, ignoring wake word detection");
                            return;
                        }

                        setKeywordDetection(true);
                        setTimeout(() => {
                            setKeywordDetection(false);
                        }, 2000);
                        break;
                }
            } catch (e) {
                console.error("Error parsing wake word message:", e);
            }
        };

        openWakeWordWS.current.onopen = () => {
            console.log("OpenWakeWord connection established");
        };

        openWakeWordWS.current.onerror = (error) => {
            console.error("OpenWakeWord error:", error);
        };

        openWakeWordWS.current.onclose = () => {
            console.log("OpenWakeWord connection closed");
        };

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
                    }, 2000);
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
            }, 2000);

            return () => {
                recognition.abort();
            }
        };
    }, []);

    useEffect(() => {
        if (window.location.pathname === "/") {
            if (!speaking) {
                if (landPageStep === 0) {
                    sendMessage({ type: "presentation1" });
                    setTimeout(() => {
                        setLandPageStep(1);
                    }, 1000);
                }
            }
        }
    }, [speaking]);

    useEffect(() => {
        if (!speaking) {
            resetNoExecutionsTimeout();
            if (intent === "unknown") {
                setIntent("");
                startListening();
            } else if (intent === "ask") {
                setIntent("");
                startListening();
            } else if (intent === "next_exercise") {
                setIntent("");
                startListening();
            } else if (intent === "help_exercise") {
                setIntent("");
                startListening();
            } else if (intent === "do_you_need_help") {
                lastIntentRef.current = intent;
                setIntent("");
                startListening();
            } else if (intent === "help_requested") {
                setIntent("");
                startListening();
            } else if (intent === "deny") {
                clearNoExecutionsTimeout();
                setIntent("");
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
    }, [sendMessage, setTextColor, startListening, landPageStep, setLandPageStep, setSpeaking]);

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
            {listening && (
                <div className="fixed justify-center bottom-32 inset-x-0 z-50">
                    <div className="flex items-center justify-center">
                        <div className="space-y-3 bg-red-500/80 rounded-xl">
                            {interim && (
                                <div className="p-3 bg-gray-100 rounded-lg m-1.5">
                                    <p className="text-gray-800 italic font-medium">{interim}</p>
                                </div>
                            )}
                            {finalText && (
                                <div className="p-3 bg-green-50 rounded-lg m-1.5">
                                    <p className="text-green-600 italic font-bold">{finalText}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
            <div className="fixed justify-center bottom-12 inset-x-0 z-50">
                <div className="flex items-center justify-center">
                    <div
                        className="w-14 h-14 rounded-full shadow-xl/20 z-50"
                        style={{
                            backgroundColor: speaking
                                ? "rgba(47, 240, 45, 0.8)"
                                : listening
                                    ? "rgba(245, 39, 67, 0.8)"
                                    : "rgba(16, 89, 231, 0.8)",
                            transition: "background-color 1s ease"
                        }}
                    >
                    </div>
                    <motion.div
                        animate={controls}
                        className="fixed w-14 h-14 rounded-full z-51 opacity-50"
                        style={{
                            backgroundColor: speaking
                                ? "rgba(47, 240, 45, 0.8)"
                                : listening
                                    ? "rgba(245, 39, 67, 0.8)"
                                    : "rgba(16, 89, 231, 0.8)",
                            transition: "background-color 1s ease"
                        }}
                    >
                    </motion.div>
                </div>
            </div>
        </>
    )
}
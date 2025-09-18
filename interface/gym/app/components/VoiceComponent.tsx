"use client"

import { useEffect, useState, useRef } from "react"
import { usePorcupine } from "@picovoice/porcupine-react"

const ACCESS_KEY = process.env.PORCUPINE_ACCESS_KEY || "";
const modelFilePath = "/porcupine_params_pt.pv";
const keywordFilePath = "/Ola-Jim_pt_wasm_v3_0_0.ppn";

if (ACCESS_KEY === "") {
    throw new Error("Missing Porcupine AccessKey. Please add it to your environment variables.");
}

export default function VoiceComponent() {

    const [listening, setListening] = useState(false);
    const [interim, setInterim] = useState("");
    const [finalText, setFinalText] = useState("");
    const recognitionRef = useRef<any>(null);

    const {
        keywordDetection,
        isLoaded,
        isListening,
        error,
        init,
        start,
        stop,
        release,
    } = usePorcupine();

    useEffect(() => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error("Speech Recognition API not supported in this browser.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.lang = 'pt-PT';
        recognition.continuous = false;
        recognition.interimResults = true;

        interface SpeechRecognitionResult {
            isFinal: boolean;
            [index: number]: {
                transcript: string;
            };
        }

        interface SpeechRecognitionEvent extends Event {
            resultIndex: number;
            results: SpeechRecognitionResult[];
        }

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
                // acrescenta ao final consolidado
                setFinalText((prev: string) => (prev ? prev + " " + finalTranscript : finalTranscript));
            }
            setInterim(interimTranscript);
        };

        recognition.onerror = (event: any) => {
            console.error("Speech recognition error:", event.error);
        };

        recognition.onend = () => {
            setTimeout(() => {
                setListening(false);
                recognitionRef.current.stop();
                setInterim("");
                setFinalText("");
            }, 1000);
        }

        return () => {
            recognition.abort();
        }
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

    const startListening = () => {
        if (recognitionRef.current && !listening) {
            try {
                recognitionRef.current.start();
                setListening(true);
                setInterim("");
            } catch (e) {
                console.error("Error starting recognition:", e);
            }
        }
    };

    useEffect(() => {
        if (keywordDetection) {
            console.log("Detected:", keywordDetection.label);
            startListening();
        }
    }, [keywordDetection]);

    useEffect(() => {
        if (error) {
            console.error(error);
        }
    }, [error]);

    return (
        <>
            {listening && (
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
            )}
        </>
    )
}
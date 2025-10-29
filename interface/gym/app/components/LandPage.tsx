"use client"
import { useEffect, useState, useRef, useCallback } from "react";
import { useColor } from "../contexts/ColorContext";
import { useLandPage } from "../contexts/LandPageContext";
import Typewriter from 'typewriter-effect';
import GymAPIClient from "../classes/apis/gymAPIClient";
import { useVoice } from "../contexts/VoiceContext";
import { motion } from "framer-motion";

export default function LandPage() {
    const { textColor } = useColor();
    const { landPageStep } = useLandPage();
    const { speaking } = useVoice();

    const timer = useRef<NodeJS.Timeout | null>(null);
    const [timerFlag, setTimerFlag] = useState(false);

    const [typewritter, setTypewritter] = useState(true);
    const [typewritter2, setTypewritter2] = useState(true);

    const [onComplete, setOnComplete] = useState(false);
    const [showIndicators, setShowIndicators] = useState(true);

    useEffect(() => {
        if (speaking) {
            setShowIndicators(false);
        }
    }, [speaking]);

    const resetTimer = useCallback(() => {
        if (timer.current) clearTimeout(timer.current);
        setTimerFlag(false);
        setTypewritter2(false);
        const newTimer = setTimeout(() => {
            setTimerFlag(true);
            setTypewritter2(true);
        }, 30000);
        timer.current = newTimer;
    }, []);

    const clearTimer = useCallback(() => {
        if (timer.current) {
            clearTimeout(timer.current);
            timer.current = null;
        }
        setTimerFlag(false);
    }, []);

    useEffect(() => {

        //GymAPIClient.startExercise();

        const checkAndRequestPermissions = async () => {
            try {
                // Check if permissions are already granted
                const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName });
                const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });

                if (cameraPermission.state === 'granted' && microphonePermission.state === 'granted') {
                    console.log("Permissions already granted");
                    return true;
                }
            } catch (error) {
                console.log("Permission API not supported", error);
            }

            // Request permissions if not already granted
            const askPermissions = async () => {
                return new Promise<void>((resolve, reject) => {
                    navigator.mediaDevices.getUserMedia({ audio: true, video: true })
                        .then(() => {
                            resolve()
                        })
                        .catch((error) => {
                            reject(error)
                        })
                })
            }

            askPermissions().then(() => {
                console.log("Microphone and camera permission granted");
                return true;
            }).catch((error) => {
                console.error("Microphone permission denied", error);
                alert("Microphone permission is required for voice commands. Please allow microphone access and refresh the page.");
                return false;
            });
        };

        checkAndRequestPermissions();

    }, []);

    useEffect(() => {
        if (landPageStep !== 6 && landPageStep !== 0) {
            setTypewritter(true);
        }
        if (landPageStep > 1 && landPageStep < 6) {
            resetTimer();
        } else {
            clearTimer();
        }
    }, [landPageStep]);

    const typewriterAnimation = (text1: string, size: string = "text-4xl", flag: boolean, onComplete?: () => void) => {
        return (
            <>
                {flag ? (
                    <Typewriter
                        onInit={(typewriter) => {
                            typewriter
                                .typeString(text1)
                                .callFunction(() => {
                                    setTypewritter(false);
                                    if (onComplete) onComplete();
                                })
                                .start();
                        }}
                        options={{
                            wrapperClassName: `${size}`,
                            cursorClassName: `${size}`,
                            delay: 50,
                        }}
                    />
                ) : (
                    <p className={`${size} ${textColor}`} dangerouslySetInnerHTML={{ __html: text1 }}></p>
                )}
            </>
        );
    };

    return (
        <main>
            <div className="flex min-h-screen flex-col items-center justify-center">
                <div className="z-10 w-full max-w-5xl items-center font-mono">
                    {landPageStep < 1 && (
                        typewriterAnimation(
                            "Bem-vindo!<br /><br />Para iniciar por favor diga \"Olá Jim\"",
                            "text-4xl",
                            typewritter,
                            () => setTimeout(() => {
                                setOnComplete(true)
                            }, 3000)
                        )
                    )}
                    {landPageStep === 1 && (
                        typewriterAnimation(
                            "Vamos tentar? Diga \"Olá Jim\"!",
                            "text-4xl",
                            typewritter
                        )
                    )}
                    {landPageStep === 2 && (
                        <>
                            {typewriterAnimation(
                                "O que comeu hoje de manhã?<br /><br />",
                                "text-4xl",
                                typewritter
                            )}
                            {timerFlag ? (
                                typewriterAnimation(
                                    "(Dica: Experimente começar com \"Olá Jim\")",
                                    "text-2xl",
                                    typewritter2
                                )
                            ) : (
                                <br />
                            )}
                        </>
                    )}
                    {landPageStep === 3 &&
                        <>
                            {typewriterAnimation(
                                "Qual é a sua cor preferida?<br /><br />",
                                "text-4xl",
                                typewritter
                            )}
                            {timerFlag ? (
                                typewriterAnimation(
                                    "(Dica: Experimente começar com \"Olá Jim\")",
                                    "text-2xl",
                                    typewritter2
                                )
                            ) : (
                                <br />
                            )}
                        </>
                    }
                    {landPageStep === 4 &&
                        <>
                            {typewriterAnimation(
                                "Diga quando quiser começar o treino<br /><br />",
                                "text-4xl",
                                typewritter
                            )}
                            {timerFlag ? (
                                typewriterAnimation(
                                    "(Dica: Experimente começar com \"Olá Jim\")",
                                    "text-2xl",
                                    typewritter2
                                )
                            ) : (
                                <br />
                            )}
                        </>
                    }
                    {landPageStep > 4 &&
                        <>
                            {typewriterAnimation(
                                "Tem a certeza que quer começar o treino?<br /><br />",
                                "text-4xl",
                                typewritter
                            )}
                            {timerFlag ? (
                                typewriterAnimation(
                                    "(Dica: Experimente começar com \"Olá Jim\")",
                                    "text-2xl",
                                    typewritter2
                                )
                            ) : (
                                <br />
                            )}
                        </>
                    }
                </div>
            </div>
            {showIndicators && landPageStep < 1 && onComplete && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 5 }}
                >
                    <div className="fixed justify-center items-center bottom-3 inset-x-0 z-50 flex-col font-mono">
                        <div className="flex items-end justify-evenly  text-xl uppercase mt-20">
                            <div className="flex-col justify-center text-center">
                                <div className="flex justify-center">
                                    <div
                                        className="w-14 h-14 rounded-full shadow-xl/20 z-50"
                                        style={{
                                            backgroundColor: "rgba(47, 240, 45, 0.8)",
                                            transition: "background-color 1s ease"
                                        }}
                                    >
                                    </div>
                                </div>
                                <div>
                                    <p className="text-center mb-2 text-white">A falar</p>
                                </div>
                            </div>
                            <div className="flex-col justify-center text-center">
                                <div className="flex justify-center">
                                    <div
                                        className="w-14 h-14 rounded-full shadow-xl/20 z-50"
                                        style={{
                                            backgroundColor: "rgba(16, 89, 231, 0)",
                                            transition: "background-color 1s ease"
                                        }}
                                    >
                                    </div>
                                </div>
                                <div>
                                    <p className="text-center mb-2 text-white">À espera</p>
                                </div>
                            </div>
                            <div className="flex-col justify-center text-center">
                                <div className="flex justify-center">
                                    <div
                                        className="w-14 h-14 rounded-full shadow-xl/20 z-50"
                                        style={{
                                            backgroundColor: "rgba(245, 39, 67, 0.8)",
                                            transition: "background-color 1s ease"
                                        }}
                                    >
                                    </div>
                                </div>
                                <div>
                                    <p className="text-center mb-2 text-white">A ouvir</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </main>
    );
}

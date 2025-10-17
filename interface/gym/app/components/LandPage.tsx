"use client"
import { useEffect, useState, useRef, useCallback } from "react";
import { useColor } from "../contexts/ColorContext";
import { useLandPage } from "../contexts/LandPageContext";
import Typewriter from 'typewriter-effect';
import GymAPIClient from "../classes/apis/gymAPIClient";

export default function LandPage() {
    const { textColor } = useColor();
    const { landPageStep } = useLandPage();

    const timer = useRef<NodeJS.Timeout | null>(null);
    const [timerFlag, setTimerFlag] = useState(false);

    const [typewritter, setTypewritter] = useState(true);
    const [typewritter2, setTypewritter2] = useState(true);

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

    const typewriterAnimation = (text1: string, size: string = "text-4xl", flag: boolean) => {
        return (
            <>
                {flag ? (
                    <Typewriter
                        onInit={(typewriter) => {
                            typewriter
                                .typeString(text1)
                                .callFunction(() => {
                                    setTypewritter(false);
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
        <main className="flex min-h-screen flex-col items-center justify-center">
            <div className="z-10 w-full max-w-5xl items-center font-mono">
                {landPageStep < 1 && (
                    typewriterAnimation(
                        "Bem-vindo!<br /><br />Para iniciar por favor diga \"Olá Jim\"",
                        "text-4xl",
                        typewritter
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
        </main>
    );
}

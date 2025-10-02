"use client"
import { useEffect } from "react";
import { useColor } from "../contexts/ColorContext";
import { useLandPage } from "../contexts/LandPageContext";

export default function LandPage() {
    const { textColor } = useColor();
    const { landPageStep, setLandPageStep } = useLandPage();

    useEffect(() => {

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

    return (
        <main className="flex min-h-screen flex-col items-center justify-center">
            <div className="z-10 w-full max-w-5xl items-center font-mono">
                <p className={`text-4xl ${textColor}`}>
                    Bem-vindo!
                    <br />
                    <br />
                    Para iniciar por favor diga &quot;Olá Jim&quot;
                </p>
            </div>
        </main>
    );
}

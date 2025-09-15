"use client"

import { useEffect, useRef, useState } from 'react';
import { WebSocketSignalingClient } from '../utils/websocket'

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

export default function TestComp() {
    const videoRef = useRef<HTMLVideoElement>(null);
    const displayStreamRef = useRef<MediaStream>(null);
    const [counter, setCounter] = useState(0);
    const [isStreaming, setIsStreaming] = useState(false);
    const pcRef = useRef<RTCPeerConnection | null>(null);

    const signalingRef = useRef<WebSocketSignalingClient | null>(null);
    const dataChannelRef = useRef<RTCDataChannel | null>(null);

    useEffect(() => {

        const startConnection = async () => {
            pcRef.current = new RTCPeerConnection(pc_config);

            const videoTrack = displayStreamRef.current?.getVideoTracks()[0];


            if (pcRef.current) {
                pcRef.current.addTrack(videoTrack!, displayStreamRef.current!);
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
        };

        const startWebcam = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: true, 
                    audio: false 
                });
                
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    displayStreamRef.current = stream;
                    setIsStreaming(true);
                }

                startConnection();
            } catch (error) {
                console.error('Error accessing webcam:', error);
            }
        };

        startWebcam();

        // Cleanup function to stop the stream when component unmounts
        return () => {
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject as MediaStream;
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const incrementCounter = () => {
        setCounter(prev => prev + 1);
    };

    return (
        <main className="relative w-full h-screen flex flex-col items-center justify-center bg-black">
            <div className="relative">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="max-w-full max-h-[80vh] rounded-lg shadow-lg"
                />
                
                {/* Counter overlay */}
                <div className="absolute top-4 left-4 bg-black bg-opacity-70 text-white px-4 py-2 rounded-lg text-2xl font-bold">
                    Count: {counter}
                </div>
                
                {/* Status indicator */}
                {!isStreaming && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-50 rounded-lg">
                        <p className="text-white text-lg">Starting webcam...</p>
                    </div>
                )}
            </div>
            
            {/* Increment button */}
            <button
                onClick={incrementCounter}
                className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors duration-200"
            >
                Increment Counter
            </button>
        </main>
    );
}
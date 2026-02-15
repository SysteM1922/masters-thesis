"use client"

import { createContext, useContext, useRef, ReactNode, useCallback, useState } from 'react';

interface VoiceContextType {
    sendMessage: (message: Record<string, string>) => void;
    setWebSocket: (ws: WebSocket) => void;
    onVoiceCommand: (callback: (command: string) => void) => () => void;
    notifyVoiceCommand: (command: string) => void;
    speaking: boolean;
    setSpeaking: (speaking: boolean) => void;
    onSpeakingChange: (callback: (speaking: boolean) => void) => () => void;
    startListening: () => void;
    setStartListeningFunction: (fn: () => void) => void;
    startNoExecutionsTimeout: () => void;
    resetNoExecutionsTimeout: () => void;
    clearNoExecutionsTimeout: () => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export function VoiceProvider({ children }: { children: ReactNode }) {
    const wsRef = useRef<WebSocket | null>(null);
    const callbacksRef = useRef<Set<(command: string) => void>>(new Set());
    const speakingCallbacksRef = useRef<Set<(speaking: boolean) => void>>(new Set());
    const startListeningFunctionRef = useRef<(() => void) | null>(null);
    const [speaking, setSpeakingState] = useState(false);

    const NO_EXECUTIONS_TIMEOUT = 62; // seconds
    const noExecutionsTimer = useRef<NodeJS.Timeout | null>(null);
    const helpMessageCounter = useRef(0);
    const MAX_HELP_MESSAGES = 2;

    const startNoExecutionsTimeout = () => {
        console.log('Starting no executions timeout');
        if (noExecutionsTimer.current) {
            helpMessageCounter.current -= 1;
            clearTimeout(noExecutionsTimer.current);
        }
        if (helpMessageCounter.current < MAX_HELP_MESSAGES) {
            noExecutionsTimer.current = setTimeout(() => {
                sendMessage({ type: "do_you_need_help" });
                startNoExecutionsTimeout();
                helpMessageCounter.current += 1;
            }, NO_EXECUTIONS_TIMEOUT * 1000);
        }
    }

    const clearNoExecutionsTimeout = () => {
        console.log('Clearing no executions timeout');
        if (noExecutionsTimer.current) {
            clearTimeout(noExecutionsTimer.current);
            noExecutionsTimer.current = null;
        }
    }

    const resetNoExecutionsTimeout = () => {
        console.log('Resetting no executions timeout');
        if (noExecutionsTimer.current) {
            helpMessageCounter.current = 0;
            startNoExecutionsTimeout();
        }
    }

    const setWebSocket = (ws: WebSocket) => {
        wsRef.current = ws;
    };

    const sendMessage = (message: Record<string, string>) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected');
        }
    };

    const setSpeaking = useCallback((newSpeaking: boolean) => {
        setSpeakingState(newSpeaking);
        speakingCallbacksRef.current.forEach(callback => {
            callback(newSpeaking);
        });
    }, []);

    const onVoiceCommand = useCallback((callback: (command: string) => void) => {
        callbacksRef.current.add(callback);

        return () => {
            callbacksRef.current.delete(callback);
        };
    }, []);

    const onSpeakingChange = useCallback((callback: (speaking: boolean) => void) => {
        speakingCallbacksRef.current.add(callback);

        return () => {
            speakingCallbacksRef.current.delete(callback);
        };
    }, []);

    const notifyVoiceCommand = useCallback((command: string) => {
        callbacksRef.current.forEach(callback => {
            callback(command);
        });
    }, []);

    const setStartListeningFunction = (fn: () => void) => {
        startListeningFunctionRef.current = fn;
    };

    const startListening = () => {
        if (startListeningFunctionRef.current) {
            startListeningFunctionRef.current();
        } else {
            console.warn('Start listening function not set');
        }
    };

    return (
        <VoiceContext.Provider value={{
            sendMessage,
            setWebSocket,
            onVoiceCommand,
            notifyVoiceCommand,
            speaking,
            setSpeaking,
            onSpeakingChange,
            startListening,
            setStartListeningFunction,
            resetNoExecutionsTimeout,
            startNoExecutionsTimeout,
            clearNoExecutionsTimeout,
        }}>
            {children}
        </VoiceContext.Provider>
    );
}

export function useVoice() {
    const context = useContext(VoiceContext);
    if (context === undefined) {
        throw new Error('useVoice must be used within a VoiceProvider');
    }
    return context;
}

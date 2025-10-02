"use client"

import { createContext, useContext, useRef, ReactNode, useCallback } from 'react';

interface VoiceContextType {
    sendMessage: (message: Record<string, string>) => void;
    setWebSocket: (ws: WebSocket) => void;
    onVoiceCommand: (callback: (command: string) => void) => () => void;
    notifyVoiceCommand: (command: string) => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export function VoiceProvider({ children }: { children: ReactNode }) {
    const wsRef = useRef<WebSocket | null>(null);
    const callbacksRef = useRef<Set<(command: string) => void>>(new Set());

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

    const onVoiceCommand = useCallback((callback: (command: string) => void) => {
        callbacksRef.current.add(callback);
        
        return () => {
            callbacksRef.current.delete(callback);
        };
    }, []);

    const notifyVoiceCommand = useCallback((command: string) => {
        callbacksRef.current.forEach(callback => {
            callback(command);
        });
    }, []);

    return (
        <VoiceContext.Provider value={{ 
            sendMessage, 
            setWebSocket, 
            onVoiceCommand,
            notifyVoiceCommand,
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

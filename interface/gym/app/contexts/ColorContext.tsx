"use client"
import { createContext, useContext, useState, ReactNode } from 'react';

interface ColorContextType {
    textColor: string;
    setTextColor: (color: string) => void;
}

const ColorContext = createContext<ColorContextType | undefined>(undefined);

export const ColorProvider = ({ children }: { children: ReactNode }) => {
    const [textColor, setTextColor] = useState("text-white");

    return (
        <ColorContext.Provider value={{ textColor, setTextColor }}>
            {children}
        </ColorContext.Provider>
    );
};

export const useColor = () => {
    const context = useContext(ColorContext);
    if (!context) {
        throw new Error('useColor must be used within a ColorProvider');
    }
    return context;
};
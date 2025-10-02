"use client"

import { createContext, useContext, useState, ReactNode } from 'react';

interface LandPageContextType {
    landPageStep: number;
    setLandPageStep: (step: number) => void;
}

const LandPageContext = createContext<LandPageContextType | undefined>(undefined);

export const LandPageProvider = ({ children }: { children: ReactNode }) => {
    const [landPageStep, setLandPageStep] = useState(0);
    
    return (
        <LandPageContext.Provider value={{ landPageStep, setLandPageStep }}>
            {children}
        </LandPageContext.Provider>
    );
};

export const useLandPage = () => {
    const context = useContext(LandPageContext);
    if (!context) {
        throw new Error('useLandPage must be used within a LandPageProvider');
    }
    return context;
};
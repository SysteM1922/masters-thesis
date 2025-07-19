// smoothing.js - Sistema de suavização para pose landmarks

class PoseSmoothingFilter {
    constructor(options = {}) {
        this.minCutoff = options.minCutoff || 1.0;
        this.beta = options.beta || 0.5;
        this.derivateCutoff = options.derivateCutoff || 1.0;
        this.filters = new Map();
        this.previousLandmarks = null;
        this.timestamp = 0;
        
        // Configurações de confiança
        this.confidenceThreshold = options.confidenceThreshold || 0.5;
        this.stabilizationFrames = options.stabilizationFrames || 3;
        this.landmarkHistory = [];
        this.maxHistorySize = 5;
    }

    // Filtro One Euro para suavização individual de pontos
    oneEuroFilter(value, previousValue, previousDerivate, timestamp, alpha, alphaD) {
        if (previousValue === null) {
            return { value, derivate: 0 };
        }

        const dt = timestamp - this.previousTimestamp || 1;
        const derivate = (value - previousValue) / dt;
        const smoothedDerivate = previousDerivate + alpha * (derivate - previousDerivate);
        const smoothedValue = previousValue + alphaD * (value - previousValue);

        return {
            value: smoothedValue,
            derivate: smoothedDerivate
        };
    }

    // Calcula alpha baseado na frequência de corte
    calculateAlpha(cutoff, dt) {
        const rc = 1.0 / (2 * Math.PI * cutoff);
        return dt / (dt + rc);
    }

    // Suavização principal dos landmarks
    smoothLandmarks(landmarks, confidence = 1.0, timestamp = Date.now()) {
        if (!landmarks || landmarks.length === 0) {
            return landmarks;
        }

        // Se a confiança é muito baixa, usar landmarks anteriores ou aplicar suavização mais agressiva
        if (confidence < this.confidenceThreshold && this.previousLandmarks) {
            return this.blendWithPrevious(landmarks, this.previousLandmarks, confidence);
        }

        const dt = timestamp - this.timestamp || 1;
        this.timestamp = timestamp;

        const smoothedLandmarks = landmarks.map((landmark, index) => {
            const key = index;
            
            if (!this.filters.has(key)) {
                this.filters.set(key, {
                    x: { value: landmark.x, derivate: 0 },
                    y: { value: landmark.y, derivate: 0 },
                    z: { value: landmark.z || 0, derivate: 0 }
                });
                return landmark;
            }

            const filter = this.filters.get(key);
            
            // Calcular velocidade para ajustar parâmetros dinamicamente
            const velocity = this.calculateVelocity(landmark, filter, dt);
            const adaptiveBeta = this.beta + velocity * 0.1; // Aumenta beta com velocidade
            
            // Calcular alphas
            const cutoff = this.minCutoff + adaptiveBeta * Math.abs(filter.x.derivate);
            const alpha = this.calculateAlpha(cutoff, dt);
            const alphaD = this.calculateAlpha(this.derivateCutoff, dt);

            // Aplicar filtro One Euro para cada coordenada
            const filteredX = this.oneEuroFilter(
                landmark.x, filter.x.value, filter.x.derivate, timestamp, alpha, alphaD
            );
            const filteredY = this.oneEuroFilter(
                landmark.y, filter.y.value, filter.y.derivate, timestamp, alpha, alphaD
            );
            const filteredZ = this.oneEuroFilter(
                landmark.z || 0, filter.z.value, filter.z.derivate, timestamp, alpha, alphaD
            );

            // Atualizar filtros
            filter.x = filteredX;
            filter.y = filteredY;
            filter.z = filteredZ;

            return {
                x: filteredX.value,
                y: filteredY.value,
                z: filteredZ.value,
                visibility: landmark.visibility
            };
        });

        // Aplicar suavização temporal adicional
        const temporallySmoothedLandmarks = this.applyTemporalSmoothing(smoothedLandmarks);
        
        this.previousLandmarks = temporallySmoothedLandmarks;
        this.addToHistory(temporallySmoothedLandmarks);
        
        return temporallySmoothedLandmarks;
    }

    // Calcula velocidade do movimento
    calculateVelocity(landmark, filter, dt) {
        const dx = landmark.x - filter.x.value;
        const dy = landmark.y - filter.y.value;
        return Math.sqrt(dx * dx + dy * dy) / dt;
    }

    // Mistura landmarks atuais com anteriores baseado na confiança
    blendWithPrevious(currentLandmarks, previousLandmarks, confidence) {
        const blendFactor = confidence / this.confidenceThreshold;
        
        return currentLandmarks.map((landmark, index) => {
            if (index >= previousLandmarks.length) return landmark;
            
            const prev = previousLandmarks[index];
            return {
                x: prev.x * (1 - blendFactor) + landmark.x * blendFactor,
                y: prev.y * (1 - blendFactor) + landmark.y * blendFactor,
                z: (prev.z || 0) * (1 - blendFactor) + (landmark.z || 0) * blendFactor,
                visibility: landmark.visibility
            };
        });
    }

    // Adiciona landmarks ao histórico
    addToHistory(landmarks) {
        this.landmarkHistory.push(landmarks);
        if (this.landmarkHistory.length > this.maxHistorySize) {
            this.landmarkHistory.shift();
        }
    }

    // Suavização temporal usando média ponderada do histórico
    applyTemporalSmoothing(landmarks) {
        if (this.landmarkHistory.length < 2) {
            return landmarks;
        }

        const weights = [0.4, 0.3, 0.2, 0.1]; // Pesos decrescentes para frames anteriores
        
        return landmarks.map((landmark, landmarkIndex) => {
            let weightedX = landmark.x * weights[0];
            let weightedY = landmark.y * weights[0];
            let weightedZ = (landmark.z || 0) * weights[0];
            let totalWeight = weights[0];

            // Aplicar pesos dos frames anteriores
            for (let historyIndex = 0; historyIndex < Math.min(this.landmarkHistory.length, weights.length - 1); historyIndex++) {
                const historyLandmarks = this.landmarkHistory[this.landmarkHistory.length - 1 - historyIndex];
                if (historyLandmarks && historyLandmarks[landmarkIndex]) {
                    const historyLandmark = historyLandmarks[landmarkIndex];
                    const weight = weights[historyIndex + 1];
                    
                    weightedX += historyLandmark.x * weight;
                    weightedY += historyLandmark.y * weight;
                    weightedZ += (historyLandmark.z || 0) * weight;
                    totalWeight += weight;
                }
            }

            return {
                x: weightedX / totalWeight,
                y: weightedY / totalWeight,
                z: weightedZ / totalWeight,
                visibility: landmark.visibility
            };
        });
    }

    // Detecta e corrige outliers
    detectAndCorrectOutliers(landmarks) {
        if (!this.previousLandmarks || this.landmarkHistory.length < 2) {
            return landmarks;
        }

        const maxMovement = 0.1; // Máximo movimento permitido entre frames (10% da tela)
        
        return landmarks.map((landmark, index) => {
            const prev = this.previousLandmarks[index];
            if (!prev) return landmark;

            const distance = Math.sqrt(
                Math.pow(landmark.x - prev.x, 2) + 
                Math.pow(landmark.y - prev.y, 2)
            );

            // Se o movimento é muito grande, é provavelmente um outlier
            if (distance > maxMovement) {
                // Usar interpolação com o histórico
                return this.interpolateFromHistory(index, landmark);
            }

            return landmark;
        });
    }

    // Interpola landmark usando histórico quando detecta outlier
    interpolateFromHistory(landmarkIndex, currentLandmark) {
        if (this.landmarkHistory.length < 2) {
            return currentLandmark;
        }

        // Usar média dos últimos frames válidos
        let sumX = 0, sumY = 0, sumZ = 0, count = 0;
        
        for (let i = Math.max(0, this.landmarkHistory.length - 3); i < this.landmarkHistory.length; i++) {
            const landmarks = this.landmarkHistory[i];
            if (landmarks && landmarks[landmarkIndex]) {
                const landmark = landmarks[landmarkIndex];
                sumX += landmark.x;
                sumY += landmark.y;
                sumZ += landmark.z || 0;
                count++;
            }
        }

        if (count > 0) {
            return {
                x: sumX / count,
                y: sumY / count,
                z: sumZ / count,
                visibility: currentLandmark.visibility
            };
        }

        return currentLandmark;
    }

    // Reset do filtro (útil quando há mudanças bruscas intencionais)
    reset() {
        this.filters.clear();
        this.previousLandmarks = null;
        this.landmarkHistory = [];
        this.timestamp = 0;
    }

    // Configurar parâmetros dinamicamente
    setParameters(minCutoff, beta, derivateCutoff) {
        this.minCutoff = minCutoff;
        this.beta = beta;
        this.derivateCutoff = derivateCutoff;
    }
}

// Exemplo de uso no seu código main.js
class PoseTrackingManager {
    constructor() {
        this.smoothingFilter = new PoseSmoothingFilter({
            minCutoff: 1.0,        // Frequência de corte mínima
            beta: 0.7,             // Responsividade a mudanças rápidas
            derivateCutoff: 1.0,   // Frequência de corte para derivada
            confidenceThreshold: 0.7,
            stabilizationFrames: 3
        });
    }

    processPoseData(landmarks, confidence = 1.0) {
        // Detectar e corrigir outliers primeiro
        const cleanLandmarks = this.smoothingFilter.detectAndCorrectOutliers(landmarks);
        
        // Aplicar suavização
        const smoothedLandmarks = this.smoothingFilter.smoothLandmarks(
            cleanLandmarks, 
            confidence, 
            Date.now()
        );

        return smoothedLandmarks;
    }

    // Ajustar parâmetros baseado na situação
    adjustSmoothingForScenario(scenario) {
        switch(scenario) {
            case 'high-movement': // Exercícios rápidos
                this.smoothingFilter.setParameters(0.5, 1.2, 1.5);
                break;
            case 'precise': // Movimentos precisos
                this.smoothingFilter.setParameters(2.0, 0.3, 0.5);
                break;
            case 'balanced': // Uso geral
            default:
                this.smoothingFilter.setParameters(1.0, 0.7, 1.0);
                break;
        }
    }
}

export { PoseSmoothingFilter, PoseTrackingManager };
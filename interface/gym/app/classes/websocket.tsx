class WebSocketSignalingClient {

    websocket: WebSocket | null;
    id: string | null;
    port: number;
    host: string;

    constructor(host: string, port: number, id: string) {
        this.id = id;
        this.websocket = null;
        this.port = port;
        this.host = host;
    }

    async connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
                    this.websocket.close();
                    reject(new Error('Connection timeout'));
                }
            }, 5000);

            this.websocket = new WebSocket(`ws://${this.host}:${this.port}/ws`);
            
            this.websocket.onopen = () => {
                clearTimeout(timeout);
                console.log(`Connected to signaling server at ${this.host}:${this.port}`);
                this.websocket!.send(JSON.stringify({ type: 'connect', client_id: this.id }));
                resolve();
            };

            this.websocket.onerror = (error) => {
                clearTimeout(timeout);
                console.error('WebSocket connection error:', error);
                reject(new Error('WebSocket connection failed'));
            };

            this.websocket.onclose = () => {
                clearTimeout(timeout);
                if (this.websocket?.readyState !== WebSocket.OPEN) {
                    reject(new Error('WebSocket connection closed'));
                }
            };
        });
    }

    sendMessage(obj: RTCSessionDescription | { type: string; candidate: RTCIceCandidate } | null) {
        let message = Object.create(null);

        if (obj && 'sdp' in obj) {
            message = {
                type: obj.type,
                sdp: obj.sdp,
            };
        } else {
            message = obj;
        }

        try {
            this.websocket!.send(JSON.stringify(message));
            const type = obj!.type || message.type || 'unknown';
            console.log('Sent message:', type);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }

    sendOffer(pc: RTCPeerConnection) {
        pc.createOffer()
            .then((offer) => {
                return pc.setLocalDescription(offer);
            })
            .then(() => {
                this.sendMessage(pc.localDescription);
                console.log('Offer sent to signaling server');
            })
            .catch((error) => {
                console.error('Error creating or sending offer:', error);
            });
    }

    receiveAnswer(pc: RTCPeerConnection, answer: RTCSessionDescription) {
        pc.setRemoteDescription(answer)
            .then(() => {
                console.log('Remote description set successfully');
            })
            .catch((error) => {
                console.error('Error setting remote description:', error);
            });
    }

    sendIceCandidate(candidate: RTCIceCandidate | null) {
        if (candidate == null) {
            return;
        }

        const message = {
            type: 'ice_candidate',
            candidate: candidate,
        };

        this.sendMessage(message);
    }

    handleMessages(pc: RTCPeerConnection) {

        this.websocket!.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                switch (message.type) {
                    case 'register':
                        if (message.registered) {
                            console.log('Successfully registered with signaling server');
                        } else {
                            console.error('Failed to register with signaling server');
                            this.close();
                        }
                        break;

                    case 'connecting':
                        console.log('Connecting to server:', message.unit_id);
                        break;

                    case 'accepted_connection':
                        console.log('Connection accepted by server:', message.unit_id);
                        this.sendOffer(pc);
                        break;

                    case 'answer':
                        console.log('Received answer from server');
                        this.receiveAnswer(pc, message);
                        break;

                    case 'ice_candidate':
                        console.log('Received ICE candidate from server');
                        if (message.candidate) {
                            const candidate = new RTCIceCandidate(message.candidate);
                            pc.addIceCandidate(candidate)
                                .then(() => {
                                    console.log('ICE candidate added successfully');
                                })
                                .catch((error) => {
                                    console.error('Error adding ICE candidate:', error);
                                });
                        } else {
                            console.warn('Received empty ICE candidate');
                        }
                        break;

                    case 'signaling_disconnect':
                        console.log('Signaling server disconnected');
                        this.close();
                        break;

                    case 'disconnect':
                        console.log('Server disconnected:', message.server_id);
                        this.close();
                        break;

                    case 'error':
                        console.error('Error from server:', message.message || 'Unknown error');
                        this.websocket!.close();
                        alert(message.message + '\nPlease try again later.');
                        window.location.reload();
                        break;

                    default:
                        console.log('Received message:', message);
                        break;
                }

            } catch (error) {
                console.error('Error receiving message:', error);
                this.close();
            }
        }
    }

    close() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            try {
                this.websocket.close();
                console.log('WebSocket connection closed');
            }
            catch (error) {
                console.error('Error closing WebSocket:', error);
            } finally {
                if (window.location.pathname !== "/bye") {
                    alert('Connection to signaling server lost.\nPlease reload the page.');
                    window.location.reload();
                }
            }
            this.websocket = null;
        }
    }

}

export { WebSocketSignalingClient };
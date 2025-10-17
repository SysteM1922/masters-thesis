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

    async connect() {
        this.websocket = new WebSocket(`ws://${this.host}:${this.port}/ws`);
        this.websocket.onopen = () => {
            console.log(`Connected to signaling server at ${this.host}:${this.port}`);
            this.websocket!.send(JSON.stringify({ type: 'connect', client_id: this.id }));
        };
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
        let errors = 0;

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
                        console.log('Connecting to server:', message.server_id);
                        break;

                    case 'accepted_connection':
                        console.log('Connection accepted by server:', message.server_id);
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
                        errors++;
                        if (errors > 5) {
                            console.error('Too many errors, closing connection');
                            this.close();
                        }
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
                alert("Ligação com o servidor perdida. Por favor, reinicie a aplicação.");
                window.location.reload();
            }
            this.websocket = null;
        }
    }

}

export { WebSocketSignalingClient };
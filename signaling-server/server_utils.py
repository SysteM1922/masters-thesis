import json
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket
from enum import Enum
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClientState(Enum):
    """Enumeration for client states."""
    IDLE = "idle"
    CALLING = "calling"
    IN_CALL = "in_call"
    BUSY = "busy"

@dataclass
class Client:
    id: str
    websocket: WebSocket
    state: ClientState = ClientState.IDLE
    connected_to: Optional[str] = None
    last_ping: datetime = None

    def to_dict(self):
        """Convert the client object to a dictionary."""
        return {
            "id": self.id,
            "state": self.state.value,
            "connected_to": self.connected_to,
            "last_ping": self.last_ping.isoformat() if self.last_ping else None
        }

class SignalingServer:
    def __init__(self):
        self.clients : Dict[str, Client] = {}

        self.ice_servers = [
            {
                "urls": ["stun:10.255.40.73:3478"]
            },
            {
                "urls": ["turn:10.255.40.73:3478"],
                "username": "turnuser",
                "credential": "gym456"
            }
        ]

    async def register_client(self, websocket: WebSocket, client_id: str):
        """Register a new client."""
        if client_id in self.clients:
            logger.warning(f"Client {client_id} already registered.")
            await self.disconnect_client(client_id)

        client = Client(
            id=client_id,
            websocket=websocket,
            last_ping=datetime.now()
        )

        self.clients[client_id] = client
        logger.info(f"Client {client_id} registered successfully.")

        await self.send_to_client(client_id, {
            "type": "ice_servers",
            "ice_servers": self.ice_servers
        })

        await self.send_to_client(client_id, {
            "type": "registered",
            "client_id": client_id,
            "status": "success"
        })

        return True
    
    async def disconnect_client(self, client_id: str):
        """Disconnect a client and clean up resources."""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]

        if client.connected_to:
            await self.end_call(client_id, client.connected_to)

        del self.clients[client_id]
        logger.info(f"Client {client_id} disconnected successfully.")

    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to a specific client."""
        if client_id not in self.clients:
            logger.warning(f"Client {client_id} not found for sending message.")
            return
        
        try:
            await self.clients[client_id].websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            self.disconnect_client(client_id)
            return False

    async def initiate_call(self, caller_id: str, target_id: str):
        """Initiate a call between two clients."""
        if caller_id not in self.clients or target_id not in self.clients:
            logger.warning(f"Call initiation failed: {caller_id} or {target_id} not registered.")
            return False

        caller = self.clients[caller_id]
        target = self.clients[target_id]

        if target.state != ClientState.IDLE:
            await self.send_to_client(caller_id, {
                "type": "call_error",
                "message": f"You are not available to make calls"
            })
            return False
        
        if target.state != ClientState.IDLE:
            await self.send_to_client(caller_id, {
                "type": "call_error",
                "message": f"{target_id} is not available to take calls"
            })
            return False
        
        caller.state = ClientState.CALLING
        caller.connected_to = target_id
        target.state = ClientState.CALLING
        target.connected_to = caller_id

        await self.send_to_client(target_id, {
            "type": "incoming_call",
            "from": caller_id
        })

        await self.send_to_client(caller_id, {
            "type": "call_initiated",
            "to": target_id,
        })

        logger.info(f"Call initiated from {caller_id} to {target_id}.")
        return True
    
    async def accept_call(self, client_id: str, caller_id: str):
        """Accept a call."""
        if client_id not in self.clients or caller_id not in self.clients:
            return False

        client = self.clients[client_id]
        caller = self.clients[caller_id]

        if client.state != ClientState.CALLING or caller.connected_to != caller_id or client.connected_to != client_id:
            return False
        
        client.state = ClientState.IN_CALL
        caller.state = ClientState.IN_CALL

        await self.send_to_client(caller_id, {
            "type": "call_accepted",
            "peer": client_id
        })

        await self.send_to_client(client_id, {
            "type": "call_accepted",
            "peer": caller_id
        })

        logger.info(f"Call accepted from {caller_id} by {client_id}.")
        return True
    
    async def reject_call(self, caller_id: str, client_id: str):
        """Reject a call from caller_id."""
        if caller_id not in self.clients or client_id not in self.clients:
            return False

        caller = self.clients[caller_id]
        client = self.clients[client_id]

        client.state = ClientState.IDLE
        caller.state = ClientState.IDLE
        caller.connected_to = None
        client.connected_to = None

        await self.send_to_client(caller_id, {
            "type": "call_rejected",
            "by": client_id
        })

        logger.info(f"Call from {caller_id} rejected by {client_id}.")
        return True
    
    async def end_call(self, client_id: str, peer_id: str):
        """End a call."""
        if client_id in self.clients:
            client = self.clients[client_id]
            client.state = ClientState.IDLE
            client.connected_to = None

        if peer_id in self.clients:
            peer = self.clients[peer_id]
            peer.state = ClientState.IDLE
            peer.connected_to = None

            await self.send_to_client(client_id, {
                "type": "call_ended",
                "by": client_id
            })

        logger.info(f"Call ended between {client_id} and {peer_id}.")
        return True
    
    async def forward_webrtc_message(self, sender_id: str, target_id: str, message: dict):
        """Forward WebRTC signaling messages between clients."""
        if sender_id not in self.clients or target_id not in self.clients:
            return False

        sender_client = self.clients[target_id]
        if sender_client.connected_to != target_id:
            logger.warning(f"Client {sender_id} is not connected to {target_id}.")
            return False
        
        message["from"] = sender_id

        return await self.send_to_client(target_id, message)
    
    def get_client_list(self):
        """Get a list of all registered clients."""
        return {client.to_dict() for client_id, client in self.clients.values()}
    
    async def ping_client(self, client_id: str):
        """Ping a client to check connectivity."""
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        client.last_ping = datetime.now()

        return await self.send_to_client(client_id, {
            "type": "ping"
        })

async def handle_message(message: str, client_id: str, signaling_server: SignalingServer):
    """Handle incoming signaling messages."""

    try:
        data = json.loads(message)
        msg_type = data.get("type")

        # Process the message based on its type
        if msg_type == "call":
            target_id = data.get("target_id")
            if target_id:
                await signaling_server.initiate_call(client_id, target_id)

        elif msg_type == "accept_call":
            caller_id = data.get("from")
            if caller_id:
                await signaling_server.accept_call(caller_id, client_id)

        elif msg_type == "reject_call":
            caller_id = data.get("from")
            if caller_id:
                await signaling_server.reject_call(caller_id, client_id)

        elif msg_type == "end_call":
            if client_id in signaling_server.clients:
                peer_id = signaling_server.clients[client_id].connected_to
                if peer_id:
                    await signaling_server.end_call(client_id, peer_id)

        elif msg_type in ["offer", "answer", "ice_candidate"]:
            target_id = data.get("to")
            if target_id:
                await signaling_server.forward_webrtc_message(client_id, target_id, data)

        elif msg_type == "ping":
            await signaling_server.ping_client(client_id)

        elif msg_type == "pong":
            if client_id in signaling_server.clients:
                signaling_server.clients[client_id].last_ping = datetime.now()

        else:
            logger.warning(f"Unknown message type '{msg_type}' from {client_id}: {data}")
            await signaling_server.send_to_client(client_id, {
                "type": "error",
                "message": f"Unknown message type '{msg_type}'"
            })

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message from {client_id}: {e}")
        await signaling_server.send_to_client(client_id, {
            "type": "error",
            "message": "Invalid JSON format"
        })

    except Exception as e:
        logger.error(f"Error handling message from {client_id}: {e}")
        await signaling_server.send_to_client(client_id, {
            "type": "error",
            "message": "Internal server error"
        })
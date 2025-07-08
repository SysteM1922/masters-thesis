from __future__ import annotations
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from protocol import Protocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Client:

    def __init__(self, id: str, server: ProcessingServer, websocket: WebSocket):
        self.id = id
        self.server = server
        self.websocket = websocket

    async def disconnect(self):
        """Disconnect the client from the server."""
        try:
            if self.server:
                self.server.remove_client(self.id)
                await Protocol.send_client_disconnect_message_to_server(self.server.websocket, self.id)
                logger.info(f"Client {self.id} disconnected.")
        except Exception as e:
            logger.error(f"Error disconnecting client {self.id}: {e}")

    async def server_shutdown(self, server_id: str):
        """Shutdown the client, closing the websocket connection."""
        try:
            await Protocol.send_server_disconnect_message_to_client(self.websocket, server_id)
            await self.websocket.close()
            self.server = None  # Clear the server reference
            logger.info(f"Client {self.id} shutdown.")
        except Exception as e:
            logger.error(f"Error shutting down client {self.id}: {e}")

    async def signaling_shutdown(self):
        """Shutdown the signaling connection for the client."""
        try:
            await Protocol.send_signaling_disconnect_message_to_client(self.websocket, self.id)
            logger.info(f"Client {self.id} signaling shutdown.")
        except Exception as e:
            logger.error(f"Error shutting down signaling for client {self.id}: {e}")

    async def handle_message(self, message: dict):
        """Handle incoming messages from the client."""
        try:
            logger.info(f"Received message from client {self.id}: {message.get('type', None)}")
            match message.get("type"):
                case "offer":
                    await Protocol.send_offer_to_server(self.server.websocket, self.id, message.get("sdp"))
                case "ice_candidate":
                    await Protocol.send_ice_candidate_to_server(self.server.websocket, self.id, message.get("candidate"))
                case "disconnect":
                    raise WebSocketDisconnect(f"Client {self.id} requested disconnect.")
                case _:
                    logger.warning(f"Unknown message type from client {self.id}: {message.get('type')}")
        
        except Exception as e:
            logger.error(f"Error handling message from client {self.id}: {e}")

class ProcessingServer:

    def __init__(self, id: str, signaling_server: SignalingServer, websocket: WebSocket = None):
        self.id = id
        self.websocket = websocket
        self.signaling_server = signaling_server
        self.clients: Dict[str, Client] = {}

    def add_client(self, client: Client):
        """Add a client to the processing server."""
        client.server = self  # Set the server reference in the client
        self.clients[client.id] = client
        logger.info(f"Client {client.id} added to Processing Server {self.id}.")

    def remove_client(self, client_id: str):
        """Remove a client from the processing server."""
        if client_id in self.clients:
            del self.clients[client_id]
            logger.info(f"Client {client_id} removed from Processing Server {self.id}.")
        else:
            logger.warning(f"Client {client_id} not found in Processing Server {self.id}.")

    async def disconnect(self):
        """Disconnect the processing server, closing all client connections."""
        self.signaling_server.remove_processing_server(self.id)
        for client in self.clients.values():
            try:
                await client.server_shutdown(self.id)
            except Exception as e:
                logger.error(f"Error disconnecting client {client.id}: {e}")
        self.clients.clear()
        logger.info(f"Processing Server {self.id} disconnected.")

    async def signaling_shutdown(self):
        """Shutdown the signaling server, closing the websocket connection."""
        try:
            await Protocol.send_signaling_disconnect_message_to_server(self.websocket, self.id)
            for client in self.clients.values():
                await client.signaling_shutdown()
            logger.info(f"Processing Server {self.id} signaling shutdown.")
        except Exception as e:
            logger.error(f"Error shutting down Processing Server {self.id}: {e}")

    async def accept_connection(self, message: dict):
        """Accept a connection from a client."""
        try:
            client_id = message.get("client_id")
            if not client_id:
                raise ValueError("client_id is required in the message to accept connection.")
            
            client = self.signaling_server.get_waiting_client(client_id)
            self.add_client(client)
            await Protocol.send_accept_connection_message(client.websocket, self.id)
            logger.info(f"Accepted connection from client {client.id} on Processing Server {self.id}.")
        
        except Exception as e:
            logger.error(f"Error accepting connection on Processing Server {self.id}: {e}")

    async def send_answer_to_client(self, client_id: str, sdp: str):
        """Send an answer to a client."""
        try:
            client = self.clients.get(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found in Processing Server {self.id}.")
            
            await Protocol.send_answer_to_client(client.websocket, self.id, sdp)
            logger.info(f"Sent answer to client {client_id} on Processing Server {self.id}.")
        
        except Exception as e:
            logger.error(f"Error sending answer to client {client_id} on Processing Server {self.id}: {e}")

    async def handle_message(self, message: dict):
        """Handle incoming messages from the processing server."""
        try:
            logger.info(f"Received message from Processing Server {self.id}: {message.get('type', None)}")

            match message.get("type"):
                case "accept_connection":
                    await self.accept_connection(message)
                case "answer":
                    await self.send_answer_to_client(message.get("client_id"), message.get("sdp"))
                case "ice_candidate":
                    await Protocol.send_ice_candidate_to_client(self.websocket, self.id, message.get("candidate"))
                case "disconnect":
                    raise WebSocketDisconnect(f"Processing Server {self.id} requested disconnect.")
                case _:
                    logger.warning(f"Unknown message type from Processing Server {self.id}: {message.get('type')}")
        
        except Exception as e:
            logger.error(f"Error handling message from Processing Server {self.id}: {e}")

class SignalingServerStatus(Enum):
    NO_PROCESSING_SERVERS = "Running with no Processing Servers"
    RUNNING = "Running"
    SHUTTING_DOWN = "Shutting Down"

class SignalingServer:
    
    def __init__(self):
        self.processing_servers: List[ProcessingServer] = []
        self.waiting_clients: Dict[str, Client] = {}
        self.status = SignalingServerStatus.NO_PROCESSING_SERVERS

    async def register_processing_server(self, server: ProcessingServer):
        """Register a processing server."""
        self.processing_servers.append(server)
        await Protocol.send_server_registration_message(server.websocket)
        logger.info(f"Processing Server {server.id} registered.")

        if self.status == SignalingServerStatus.NO_PROCESSING_SERVERS:
            self.status = SignalingServerStatus.RUNNING

    def get_waiting_client(self, client_id: str) -> Client | None:
        """Get a waiting client by ID."""
        return self.waiting_clients.pop(client_id, None)

    async def register_client(self, client: Client) -> bool:
        """Register a client to a processing server."""
        await Protocol.send_client_registration_message(client.websocket)

        if self.status == SignalingServerStatus.NO_PROCESSING_SERVERS:
            await Protocol.send_error_message(client.websocket, "No Processing Servers available to register the client.")
            logger.error("No Processing Servers available to register the client.")
            return False

        # order processing_servers by number of clients to find the least loaded server
        self.processing_servers.sort(key=lambda x: len(x.clients))
        server = self.processing_servers[0]

        self.waiting_clients[client.id] = client

        await Protocol.send_client_connection_message_to_server(server.websocket, client.id)
        await Protocol.send_server_connection_message_to_client(client.websocket, server.id)
        logger.info(f"Client {client.id} is connecting to Processing Server {server.id}.")
        return True

    def remove_processing_server(self, server_id: str):
        for server in self.processing_servers:
            if server.id == server_id:
                self.processing_servers.remove(server)
                logger.info(f"Processing Server {server_id} removed.")
                if not self.processing_servers:
                    self.status = SignalingServerStatus.NO_PROCESSING_SERVERS
                return
        logger.warning(f"Processing Server {server_id} not found.")

    async def handle_server_registration(self, message: dict, signaling_server: SignalingServer, websocket: WebSocket) -> ProcessingServer:
        if message.get("type") != "register":
            logger.error("First message must be of type 'register'")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'register'"
            }))
            await websocket.close()
            raise ValueError("First message must be of type 'register'")
        
        server_id = message.get("server_id")
        if not server_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "server_id is required"
            }))
            await websocket.close()
            raise ValueError("server_id is required")

        server = ProcessingServer(id=server_id, websocket=websocket, signaling_server=signaling_server)
        await self.register_processing_server(server)

        return server
    
    async def handle_client_registration(self, message: dict, websocket: WebSocket) -> List[Client, bool]:
        """Handle client registration with the signaling server."""

        if message.get("type") != "connect":
            logger.error("First message must be of type 'connect'")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'connect'"
            }))
            await websocket.close()
            raise ValueError("First message must be of type 'connect'")

        client_id = message.get("client_id")
        if not client_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "client_id is required"
            }))
            await websocket.close()
            raise ValueError("client_id is required")
        
        client = Client(id=client_id, server=None, websocket=websocket)
        ret = await self.register_client(client)
        
        return client, ret
    
    async def shutdown(self):
        """Shutdown the signaling server, disconnecting all processing servers and clients."""
        logger.info("Shutting down Signaling Server...")
        for server in self.processing_servers:
            try:
                await server.signaling_shutdown()
            except Exception as e:
                logger.error(f"Error shutting down Processing Server {server.id}: {e}")
        self.processing_servers.clear()
        self.status = SignalingServerStatus.NO_PROCESSING_SERVERS
        logger.info("Signaling Server shutdown complete.")
        self.status = SignalingServerStatus.SHUTTING_DOWN
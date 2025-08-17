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

class ProcessingUnit:

    def __init__(self, id: str, signaling_server: SignalingServer, websocket: WebSocket = None):
        self.id = id
        self.websocket = websocket
        self.signaling_server = signaling_server
        self.client: Client = None

    def add_client(self, client: Client):
        """Add a client to the processing unit."""
        client.server = self  # Set the server reference in the client
        self.client = client
        logger.info(f"Client {client.id} added to Processing Unit {self.id}.")

    def remove_client(self, client_id: str):
        """Remove a client from the processing unit."""
        if self.client and self.client.id == client_id:
            self.client = None
            logger.info(f"Client {client_id} removed from Processing Unit {self.id}.")
        else:
            logger.warning(f"Client {client_id} not found in Processing Unit {self.id}.")

    async def disconnect(self):
        """Disconnect the processing unit, closing all client connections."""
        self.signaling_server.remove_processing_unit(self.id)
        if self.client:
            try:
                await self.client.server_shutdown(self.id)
            except Exception as e:
                logger.error(f"Error disconnecting client {self.client.id}: {e}")
            self.client = None
        logger.info(f"Processing Unit {self.id} disconnected.")

    async def signaling_shutdown(self):
        """Shutdown the signaling server, closing the websocket connection."""
        try:
            await Protocol.send_signaling_disconnect_message_to_server(self.websocket, self.id)
            if self.client:
                await self.client.signaling_shutdown()
            logger.info(f"Processing Unit {self.id} signaling shutdown.")
        except Exception as e:
            logger.error(f"Error shutting down Processing Unit {self.id}: {e}")

    async def accept_connection(self, message: dict):
        """Accept a connection from a client."""
        try:
            client_id = message.get("client_id")
            if not client_id:
                raise ValueError("client_id is required in the message to accept connection.")
            
            client = self.signaling_server.get_waiting_client(client_id)
            self.add_client(client)
            await Protocol.send_accept_connection_message(client.websocket, self.id)
            logger.info(f"Accepted connection from client {client.id} on Processing Unit {self.id}.")

        except Exception as e:
            logger.error(f"Error accepting connection on Processing Unit {self.id}: {e}")

    async def send_answer_to_client(self, client_id: str, sdp: str):
        """Send an answer to a client."""
        try:
            if not self.client:
                raise ValueError(f"Client {client_id} not found in Processing Unit {self.id}.")

            await Protocol.send_answer_to_client(self.client.websocket, self.id, sdp)
            logger.info(f"Sent answer to client {client_id} on Processing Unit {self.id}.")

        except Exception as e:
            logger.error(f"Error sending answer to client {client_id} on Processing Unit {self.id}: {e}")

    async def send_ice_candidate_to_client(self, client_id: str, candidate: dict):
        """Send an ICE candidate to a client."""
        try:
            if not self.client:
                raise ValueError(f"Client {client_id} not found in Processing Unit {self.id}.")

            await Protocol.send_ice_candidate_to_client(self.client.websocket, self.id, candidate)
            logger.info(f"Sent ICE candidate to client {client_id} on Processing Unit {self.id}.")
        
        except Exception as e:
            logger.error(f"Error sending ICE candidate to client {client_id} on Processing Unit {self.id}: {e}")

    async def handle_message(self, message: dict):
        """Handle incoming messages from the processing server."""
        try:
            logger.info(f"Received message from Processing Unit {self.id}: {message.get('type', None)}")

            match message.get("type"):
                case "accept_connection":
                    await self.accept_connection(message)
                case "answer":
                    await self.send_answer_to_client(message.get("client_id"), message.get("sdp"))
                case "ice_candidate":
                    await self.send_ice_candidate_to_client(message.get("client_id"), message.get("candidate"))
                case "disconnect":
                    raise WebSocketDisconnect(f"Processing Server {self.id} requested disconnect.")
                case _:
                    logger.warning(f"Unknown message type from Processing Server {self.id}: {message.get('type')}")
        
        except Exception as e:
            logger.error(f"Error handling message from Processing Server {self.id}: {e}")

class MultiServer:

    def __init__(self):
        self.servers: Dict[str, ProcessingUnit] = {}

    def add_unit(self, server: ProcessingUnit):
        """Add a processing unit to the multi-server."""
        self.servers[server.id] = server
        logger.info(f"Processing Unit {server.id} added to MultiServer.")

    def remove_unit(self, unit_id: str):
        """Remove a processing unit from the multi-server."""
        if unit_id in self.servers:
            del self.servers[unit_id]
            logger.info(f"Processing Unit {unit_id} removed from MultiServer.")
        else:
            logger.warning(f"Processing Unit {unit_id} not found in MultiServer.")

class SignalingServerStatus(Enum):
    NO_SERVERS = "Running with no Servers"
    RUNNING = "Running"
    SHUTTING_DOWN = "Shutting Down"

class SignalingServer:
    
    def __init__(self):
        self.servers: List[MultiServer] = []
        self.waiting_clients: Dict[str, Client] = {}
        self.status = SignalingServerStatus.NO_SERVERS

    async def register_multi_server(self, server: MultiServer):
        """Register a server."""
        self.servers.append(server)
        await Protocol.send_server_registration_message(server.websocket)
        logger.info(f"Server {server.id} registered.")

        if self.status == SignalingServerStatus.NO_SERVERS:
            self.status = SignalingServerStatus.RUNNING

    def get_waiting_client(self, client_id: str) -> Client | None:
        """Get a waiting client by ID."""
        return self.waiting_clients.pop(client_id, None)

    async def register_client(self, client: Client) -> bool:
        """Register a client to a processing server."""
        await Protocol.send_client_registration_message(client.websocket)

        if self.status == SignalingServerStatus.NO_SERVERS:
            await Protocol.send_error_message(client.websocket, "No Servers available to register the client.")
            logger.error("No Servers available to register the client.")
            return False

        # order servers by number of clients to find the least loaded server
        self.servers.sort(key=lambda x: len(x.clients))
        server = self.servers[0]

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
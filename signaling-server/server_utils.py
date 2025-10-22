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

    def __init__(self, id: str, unit: ProcessingUnit, websocket: WebSocket):
        self.id = id
        self.unit = unit
        self.websocket = websocket

    async def disconnect(self):
        """Disconnect the client from the unit."""
        try:
            if self.unit:
                self.unit.remove_client(self.id)
                await Protocol.send_client_disconnect_message_to_unit(self.unit.websocket, self.id)
                logger.info(f"Client {self.id} disconnected.")
        except Exception as e:
            logger.error(f"Error disconnecting client {self.id}: {e}")

    async def unit_shutdown(self, unit_id: str):
        """Shutdown the client, closing the websocket connection."""
        try:
            await Protocol.send_unit_disconnect_message_to_client(self.websocket, unit_id)
            await self.websocket.close()
            self.unit = None  # Clear the unit reference
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
                    await Protocol.send_offer_to_unit(self.unit.websocket, self.id, message.get("sdp"))
                case "ice_candidate":
                    await Protocol.send_ice_candidate_to_unit(self.unit.websocket, self.id, message.get("candidate"))
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
        client.unit = self  # Set the unit reference in the client
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
        await self.signaling_server.remove_processing_unit(self.id)
        if self.client:
            try:
                await self.client.unit_shutdown(self.id)
            except Exception as e:
                logger.error(f"Error disconnecting client {self.client.id}: {e}")
            self.client = None
        logger.info(f"Processing Unit {self.id} disconnected.")    

    async def signaling_shutdown(self):
        """Shutdown the signaling server, closing the websocket connection."""
        try:
            await Protocol.send_signaling_disconnect_message_to_unit(self.websocket, self.id)
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
            
            if client_id != self.client.id:
                logger.warning(f"Client {client_id} is not the current client for Processing Unit {self.id}.")
                return

            await Protocol.send_accept_connection_message(self.client.websocket, self.id)
            logger.info(f"Accepted connection from client {self.client.id} on Processing Unit {self.id}.")

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
        """Handle incoming messages from the processing unit."""
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
                    raise WebSocketDisconnect(f"Processing Unit {self.id} requested disconnect.")
                case _:
                    logger.warning(f"Unknown message type from Processing Unit {self.id}: {message.get('type')}")

        except Exception as e:
            logger.error(f"Error handling message from Processing Unit {self.id}: {e}")

class MultiServer:

    def __init__(self, id, signaling_server: SignalingServer, websocket: WebSocket):
        self.processing_units: Dict[str, ProcessingUnit] = {}
        self.signaling_server = signaling_server
        self.websocket = websocket
        self.id = id

    def add_unit(self, unit: ProcessingUnit):
        """Add a processing unit to the multi-server."""
        self.processing_units[unit.id] = unit
        logger.info(f"Processing Unit {unit.id} added to MultiServer.")

    async def remove_unit(self, unit_id: str):
        """Remove a processing unit from the multi-server."""
        if unit_id in self.processing_units:
            client = self.processing_units.pop(unit_id).client
            await Protocol.send_server_unit_disconnect(self.websocket, unit_id)
            if client:
                await client.unit_shutdown(unit_id)
            logger.info(f"Processing Unit {unit_id} removed from MultiServer.")
        else:
            logger.warning(f"Processing Unit {unit_id} not found in MultiServer.")

    async def disconnect(self):
        """Disconnect the multi-server and all its processing units."""
        for unit in self.processing_units.values():
            await unit.client.disconnect() if unit.client else None

        del self.signaling_server.servers[self.id]
        if not self.signaling_server.check_multi_server_availability():
            self.signaling_server.status = SignalingServerStatus.NO_SERVERS
        logger.info(f"MultiServer disconnected.")

    async def signaling_shutdown(self):
        """Shutdown the signaling server, closing the websocket connection."""
        try:
            await Protocol.send_signaling_disconnect_message_to_server(self.websocket)
            if self.processing_units:
                for unit in self.processing_units.values():
                    await unit.signaling_shutdown()
            logger.info(f"MultiServer {self.id} signaling shutdown.")
        except Exception as e:
            logger.error(f"Error shutting down MultiServer {self.id}: {e}")

class SignalingServerStatus(Enum):
    NO_SERVERS = "Running with no Servers"
    RUNNING = "Running"
    SHUTTING_DOWN = "Shutting Down"

class SignalingServer:
    
    def __init__(self):
        self.servers: Dict[str, MultiServer] = {}
        self.waiting_clients: List[Client] = []
        self.status = SignalingServerStatus.NO_SERVERS

    async def register_multi_server(self, server: MultiServer):
        """Register a server."""
        self.servers[server.id] = server
        await Protocol.send_server_registration_message(server.websocket)
        logger.info(f"Server {server.id} registered.")

        if self.status == SignalingServerStatus.NO_SERVERS:
            self.status = SignalingServerStatus.RUNNING

    def get_waiting_client(self) -> Client | None:
        """Get oldest waiting client."""
        return self.waiting_clients.pop(0)

    async def register_client(self, client: Client) -> bool:
        """Register a client to a processing server."""
        await Protocol.send_client_registration_message(client.websocket)

        if self.status == SignalingServerStatus.NO_SERVERS:
            await Protocol.send_error_message(client.websocket, "No Servers available to register the client.")
            logger.error("No Servers available to register the client.")
            return False

        # order servers by number of clients to find the least loaded server
        server = min(self.servers.values(), key=lambda x: len(x.processing_units))
        
        self.waiting_clients.append(client)

        await Protocol.send_server_a_unit_request(server.websocket)
        logger.info(f"Client {client.id} is waiting for a Processing Unit from Server {server.id}.")
        return True
    
    async def assign_processing_unit_to_client(self, unit: ProcessingUnit):
        client = self.get_waiting_client()
        if not client:
            logger.warning(f"No waiting clients to assign to Processing Unit {unit.id}.")
            return

        await Protocol.send_client_connection_message_to_unit(unit.websocket, client.id)
        await Protocol.send_unit_connection_message_to_client(client.websocket, unit.id)

        unit.add_client(client)

        logger.info(f"Client {client.id} is connecting to Processing Server {unit.id}.")
        return True
    
    async def register_processing_unit(self, unit: ProcessingUnit, server: MultiServer):
        server.add_unit(unit)
        await Protocol.send_unit_registration_message(unit.websocket)
        logger.info(f"Processing Unit {unit.id} registered to MultiServer {server.id}.")

        await self.assign_processing_unit_to_client(unit)

    async def remove_processing_unit(self, unit_id: str):
        server_id = unit_id.split("-")[0]
        if server_id not in self.servers:
            return

        server = self.servers[server_id]
        if unit_id in server.processing_units:
            await server.remove_unit(unit_id)
            logger.info(f"Processing Unit {unit_id} removed.")
            return
        
        logger.warning(f"Processing Unit {unit_id} not found.")

    async def handle_processing_unit_registration(self, message: dict, signaling_server: SignalingServer, websocket: WebSocket) -> ProcessingUnit:
        if message.get("type") != "register":
            logger.error("First message must be of type 'register'")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'register'"
            }))
            await websocket.close()
            raise ValueError("First message must be of type 'register'")

        unit_id = message.get("unit_id")
        server_id = unit_id.split("-")[0] if unit_id else None

        if not unit_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "unit_id is required"
            }))
            await websocket.close()
            raise ValueError("unit_id is required")

        unit = ProcessingUnit(id=unit_id, websocket=websocket, signaling_server=signaling_server)
        server = signaling_server.servers.get(server_id)

        if not server:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Server not found"
            }))
            await websocket.close()
            raise ValueError("Server not found")

        try:
            await self.register_processing_unit(unit, server)
        except Exception as e:
            logger.error(f"Error registering Processing Unit {unit.id}: {e}")

        return unit

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
        
        client = Client(id=client_id, unit=None, websocket=websocket)
        ret = await self.register_client(client)
        
        return client, ret

    async def handle_multi_server_registration(self, message: dict, signaling_server: SignalingServer, websocket: WebSocket) -> MultiServer:
        if message.get("type") != "register":
            logger.error("First message must be of type 'register'")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'register'"
            }))
            await websocket.close()
            raise ValueError("First message must be of type 'register'")

        server = MultiServer(id = message.get("server_id"), websocket=websocket, signaling_server=signaling_server)
        await self.register_multi_server(server)

        return server

    async def shutdown(self):
        """Shutdown the signaling server, disconnecting all servers and clients."""
        logger.info("Shutting down Signaling Server...")
        for server in self.servers.values():
            try:
                await server.signaling_shutdown()
            except Exception as e:
                logger.error(f"Error shutting down Server {server.id}: {e}")
        self.servers.clear()
        self.status = SignalingServerStatus.NO_SERVERS
        logger.info("Signaling Server shutdown complete.")
        self.status = SignalingServerStatus.SHUTTING_DOWN

    def check_multi_server_availability(self) -> bool:
        """Check if there are available multi-servers."""
        return len(self.servers) > 0
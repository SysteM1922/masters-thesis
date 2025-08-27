from fastapi import WebSocket

class Protocol:

    @staticmethod
    async def send(websocket: WebSocket, message: dict) -> None:
        """
        Send a message to the client via WebSocket.
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            raise RuntimeError(f"Failed to send message: {e}")
        
    @staticmethod
    async def send_unit_registration_message(websocket: WebSocket) -> None:
        """
        Send a registration message for the unit.
        """
        message = {
            "type": "register",
            "registered": True,
            "message": "The unit is registered."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_client_registration_message(websocket: WebSocket) -> None:
        """
        Send a registration message for the client.
        """
        message = {
            "type": "register",
            "registered": True,
            "message": "The client is registered."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_server_registration_message(websocket: WebSocket) -> None:
        """
        Send a registration message for the server.
        """
        message = {
            "type": "register",
            "registered": True,
            "message": "The server is registered."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_client_connection_message_to_unit(websocket: WebSocket, client_id: str) -> None:
        """
        Send a connection message for the client.
        """
        message = {
            "type": "connect",
            "client_id": client_id,
            "message": "The client wants to connect."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_unit_connection_message_to_client(websocket: WebSocket, unit_id: str) -> None:
        """
        Send a connection message for the unit.
        """
        message = {
            "type": "connecting",
            "unit_id": unit_id,
            "message": "You are connecting to the unit."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_unit_disconnect_message_to_client(websocket: WebSocket, unit_id: str) -> None:
        """
        Send a disconnect message for the unit.
        """
        message = {
            "type": "disconnect",
            "unit_id": unit_id,
            "message": "The unit was disconnected."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_client_disconnect_message_to_unit(websocket: WebSocket, client_id: str) -> None:
        """
        Send a disconnect message for the unit.
        """
        message = {
            "type": "disconnect",
            "client_id": client_id,
            "message": "The client was disconnected."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_signaling_disconnect_message_to_client(websocket: WebSocket, client_id: str) -> None:
        """
        Send a signaling disconnect message to the client.
        """
        message = {
            "type": "signaling_disconnect",
            "client_id": client_id,
            "message": "The signaling connection was closed."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_signaling_disconnect_message_to_unit(websocket: WebSocket, unit_id: str) -> None:
        """
        Send a signaling disconnect message to the unit.
        """
        message = {
            "type": "signaling_disconnect",
            "unit_id": unit_id,
            "message": "The signaling connection was closed."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_signaling_disconnect_message_to_server(websocket: WebSocket) -> None:
        """
        Send a signaling disconnect message to the server.
        """
        message = {
            "type": "signaling_disconnect",
            "message": "The signaling connection was closed."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_server_a_unit_request(websocket: WebSocket) -> None:
        """
        Ask for a processing unit from the server.
        """
        message = {
            "type": "request_processing_unit",
            "message": "A client is requesting a processing unit."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_server_unit_disconnect(websocket: WebSocket, unit_id: str) -> None:
        """
        Notify the server about a unit disconnection.
        """
        message = {
            "type": "unit_disconnect",
            "unit_id": unit_id,
            "message": "A processing unit has disconnected."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_error_message(websocket: WebSocket, error_message: str) -> None:
        """
        Send an error message to the client.
        """
        message = {
            "type": "error",
            "message": error_message
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_accept_connection_message(websocket: WebSocket, unit_id: str) -> None:
        """
        Send an accept connection message to the client.
        """
        message = {
            "type": "accepted_connection",
            "unit_id": unit_id,
            "message": "The connection was accepted."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_offer_to_unit(websocket: WebSocket, client_id: str, offer: dict) -> None:
        """
        Send an offer to the unit.
        """
        message = {
            "type": "offer",
            "client_id": client_id,
            "sdp": offer,
            "message": "Offer sent to the unit."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_answer_to_client(websocket: WebSocket, unit_id: str, answer: dict) -> None:
        """
        Send an answer to the client.
        """
        message = {
            "type": "answer",
            "unit_id": unit_id,
            "sdp": answer,
            "message": "Answer sent to the client."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_ice_candidate_to_unit(websocket: WebSocket, client_id: str, candidate: dict) -> None:
        """
        Send an ICE candidate to the unit.
        """
        message = {
            "type": "ice_candidate",
            "client_id": client_id,
            "candidate": candidate,
            "message": "ICE candidate sent to the unit."
        }
        await Protocol.send(websocket, message)

    @staticmethod
    async def send_ice_candidate_to_client(websocket: WebSocket, unit_id: str, candidate: dict) -> None:
        """
        Send an ICE candidate to the client.
        """
        message = {
            "type": "ice_candidate",
            "unit_id": unit_id,
            "candidate": candidate,
            "message": "ICE candidate sent to the client."
        }
        await Protocol.send(websocket, message)
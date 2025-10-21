from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import argparse
import uvicorn
from server_utils import Client, ProcessingUnit, SignalingServer, MultiServer

logging.basicConfig(
    filename='server.log',
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

tags_metadata = []

signaling_server = SignalingServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Signaling Server...")
    yield
    await signaling_server.shutdown()

app = FastAPI(
    title="Signaling Server",
    description="A Signaling server for WebRTC applications",
    version="1.0.0",
    root_path="/signaling",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint to verify server is running."""
    return {"message": "Welcome to the Signaling Server"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}

# WebSocket endpoint for server registration
@app.websocket("/ws/server")
async def websocket_server_endpoint(websocket: WebSocket):
    await websocket.accept()
    server: Optional[MultiServer] = None

    try:
        data = await  websocket.receive_json()

        server = await signaling_server.handle_multi_server_registration(data, signaling_server, websocket)

        while True:

            data = await websocket.receive_json()

            await server.handle_message(data)

    except WebSocketDisconnect:
        if server:
            logger.info(f"Server {server.id} disconnected")
        else:
            logger.info("Server disconnected without registration")
    except Exception as e:
        logger.error(f"Error in WebSocket Server {server.id}: {e}")
    finally:
        if server:
            await server.disconnect()

@app.websocket("/ws/processing")
async def websocket_processing_endpoint(websocket: WebSocket):
    """WebSocket endpoint for server registration."""
    await websocket.accept()
    processing_unit: Optional[ProcessingUnit] = None
    try:
        data = await websocket.receive_json()

        processing_unit = await signaling_server.handle_processing_unit_registration(data, signaling_server, websocket)

        while True:
            data = await websocket.receive_json()

            await processing_unit.handle_message(data)

    except WebSocketDisconnect:
        if processing_unit:
            logger.info(f"Processing Unit {processing_unit.id} disconnected")
        else:
            logger.info("Processing Unit disconnected without registration")
    except Exception as e:
        logger.error(f"Error in WebSocket Processing Unit {processing_unit.id}: {e}")
    finally:
        if processing_unit:
            await processing_unit.disconnect()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for handling signaling messages."""
    await websocket.accept()

    client: Optional[Client] = None

    try:
        data = await websocket.receive_json()

        client, registered = await signaling_server.handle_client_registration(data, websocket)

        if registered:
            while True:
                data = await websocket.receive_json()

                await client.handle_message(data)
        else:
            logger.info(f"Client {client.id} could not be registered. No Servers available.")
            await client.signaling_shutdown()

    except WebSocketDisconnect:
        if client:
            logger.info(f"Client {client.id} disconnected")
            await client.disconnect()
        else:
            logger.info("Client disconnected without registration")
    except Exception as e:
        logger.error(f"Error in WebSocket Client {client.id}: {e}")

def main():

    parser = argparse.ArgumentParser(description="Signaling Server for WebRTC")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8765, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], help="Set the logging level")

    args = parser.parse_args()

    logger.info(f"Starting Signaling Server on {args.host}:{args.port} with log level {args.log_level}")

    uvicorn.run(
        "signaling_server:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )

if __name__ == "__main__":
    main()
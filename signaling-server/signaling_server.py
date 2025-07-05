from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import argparse
import uvicorn
import json
from server_utils import Client, ProcessingServer, SignalingServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

tags_metadata = []

signaling_server = SignalingServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Signaling Server...")
    yield
    signaling_server.shutdown()

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
    # A unique server should be stored in order to other clients to connect to its processes
    """WebSocket endpoint for server registration."""
    await websocket.accept()
    server: Optional[ProcessingServer] = None
    try:
        message = await websocket.receive_json()
        data = json.loads(message)

        server = await signaling_server.handle_server_registration(data, signaling_server, websocket)

        while True:
            message = await websocket.receive_json()
            data = json.loads(message)

            server.handle_message(data)

    except WebSocketDisconnect:
        logger.info(f"Server {server.id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
    finally:
        if server:
            server.disconnect()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for handling signaling messages."""
    await websocket.accept()

    client: Optional[Client] = None

    try:
        message = await websocket.receive_json()
        data = json.loads(message)

        client = await signaling_server.handle_client_registration(data, websocket)
        
        while True:
            message = await websocket.receive_json()
            data = json.loads(message)

            client.handle_message(data)

    except WebSocketDisconnect:
        logger.info(f"Client {client.id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket {client.id}: {e}")
    finally:
        if client:
            client.disconnect()


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
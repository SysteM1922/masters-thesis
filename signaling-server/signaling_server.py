from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import argparse
import uvicorn
import json
from server_utils import SignalingServer, handle_message

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
    logger.info("Shutting down Signaling Server...")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for handling signaling messages."""
    await websocket.accept()

    client_id = None

    try:
        message = await websocket.receive_text()
        data = json.loads(message)

        if data.get("type") != "register":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'register'"
            }))
            await websocket.close()
            return
        
        client_id = data.get("client_id")
        if not client_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "client_id is required"
            }))
            await websocket.close()
            return
        
        await signaling_server.register_client(websocket, client_id)

        async for message in websocket:
            await handle_message(message, client_id, signaling_server)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket {client_id}: {e}")
    finally:
        if client_id:
            await signaling_server.disconnect_client(client_id)

# WebSocket endpoint for server registration
@app.websocket("/ws/server")
async def websocket_server_endpoint(websocket: WebSocket):
    # A unique server should be stored in order to other cklients to connect to its processes
    """WebSocket endpoint for server registration."""
    await websocket.accept()
    try:
        message = await websocket.receive_text()
        data = json.loads(message)

        if data.get("type") != "register":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "First message must be of type 'register'"
            }))
            await websocket.close()
            return

        server_id = data.get("server_id")
        if not server_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "server_id is required"
            }))
            await websocket.close()
            return

        await signaling_server.register_server(websocket, server_id)

        async for message in websocket:
            await handle_message(message, server_id, signaling_server)

    except WebSocketDisconnect:
        logger.info(f"Server {server_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket {server_id}: {e}")
    finally:
        if server_id:
            await signaling_server.disconnect_server(server_id)

def main():

    parser = argparse.ArgumentParser(description="Signaling Server for WebRTC")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8765, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"], help="Set the logging level")

    args = parser.parse_args()

    logger.info(f"Starting Signaling Server on {args.host}:{args.port} with log level {args.log_level}")

    uvicorn.run(
        "main:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )

if __name__ == "__main__":
    main()
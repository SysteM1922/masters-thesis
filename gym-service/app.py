import argparse
from asyncio.log import logger
import logging
import sys
import time
import multiprocessing
from pystray import Icon, MenuItem, Menu
from PIL import Image
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import tts
from agent import Agent
import asyncio

load_dotenv(".env")

PORT = os.getenv("PORT", 8100)

client_ws = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

tags_metadata = []

app = FastAPI(
    title="Gym Service",
    description="A Gym Service for managing workout sessions",
    version="1.0.0",
    root_path="/gym",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost"],  # Only localhost is needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_audio_ws(websocket: WebSocket, filename: str, intent: str = None):
    if intent:
        await websocket.send_json({"type": "audio", "intent": intent})
    with open(filename, "rb") as audio_file:
        chunk = audio_file.read(4096)
        while chunk:
            await websocket.send_bytes(chunk)
            chunk = audio_file.read(4096)

@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint to verify server is running."""
    return {"message": "Welcome to the Gym Service"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "ok"}

@app.websocket("/ws/session")
async def websocket_session(websocket: WebSocket):
    """WebSocket endpoint for managing workout sessions."""
    
    global client_ws

    if client_ws is not None:
        await websocket.close(code=1000)
        return
    
    await websocket.accept()
    try:
        client_ws = websocket
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received message from client: {data}")
            match data.get("type"):
                case "new_command":
                    command = data.get("command", "")
                    response = await Agent.parse_message(command)

                    intent = response.get("intent", {}).get("name", "")
                    Agent.update_intent(intent)
                    print(f"Predicted intent: {intent}")

                    match intent:
                        case "greet":
                            filename = await tts.greet()
                            await send_audio_ws(websocket, filename, intent)

                        case "affirm":
                            if Agent._previous_intent == "next_exercise":
                                Agent._actual_exercise += 1

                            filename = await tts.affirm()
                            await send_audio_ws(websocket, filename, intent)

                        case "deny":
                            filename = await tts.affirm()
                            await send_audio_ws(websocket, filename, intent)

                        case "next_exercise":
                            filename = await tts.next_exercise()
                            print(filename)
                            await send_audio_ws(websocket, filename, intent)

                        case "help":
                            filename = await tts.help()
                            await send_audio_ws(websocket, filename, intent)

                        case "help_exercise":
                            filename = await tts.help_exercise(Agent._actual_exercise)
                            await send_audio_ws(websocket, filename, intent)

                        case "presentation":
                            filename = await tts.presentation()
                            await send_audio_ws(websocket, filename, intent)
                        
                        case "goodbye":
                            filename = await tts.goodbye()
                            await send_audio_ws(websocket, filename, intent)

                case "goodbye":
                    filename = await tts.goodbye()
                    await send_audio_ws(websocket, filename, intent)

                case "arms_exercise":
                    filename = await tts.arms_exercise()
                    await send_audio_ws(websocket, filename)

                case "legs_exercise":
                    filename = await tts.legs_exercise()
                    await send_audio_ws(websocket, filename)

                case "walk_exercise":
                    filename = await tts.walk_exercise()
                    await send_audio_ws(websocket, filename)

                case "change_legs":
                    filename = await tts.change_legs()
                    await send_audio_ws(websocket, filename)

                case "exercise_done":
                    filename = await tts.exercise_done()
                    await send_audio_ws(websocket, filename)

                case "presentation":
                    filename = await tts.presentation()
                    await send_audio_ws(websocket, filename)

                case "simple_exercise_done":
                    filename = await tts.simple_exercise_done()
                    await send_audio_ws(websocket, filename)

                case "lets_go":
                    filename = await tts.lets_go()
                    await send_audio_ws(websocket, filename)
                
                case _:
                    logger.warning(f"Unknown message type: {data.get('type')}")

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        client_ws = None
        await websocket.close()
        logger.info("WebSocket connection closed")

def start_server():
    
    parser = argparse.ArgumentParser(description="Gym Service for managing workout sessions")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error", "critical"], help="Set the logging level")

    args = parser.parse_args()

    logger.info(f"Starting Gym Service with log level {args.log_level}")

    uvicorn.run(
        "app:app" if args.reload else app,
        host="localhost",
        port=8100,
        reload=args.reload,
        log_level=args.log_level,
    )

if __name__ == "__main__":

    server_process = None

    def create_image():
        image = Image.open("images/py-logo.png")
        return image

    def quit_app(icon):
        icon.stop()
        if server_process is not None:
            server_process.terminate()
            server_process.join()
        sys.exit(0)

    menu = Menu(
        MenuItem("Sair", quit_app)
    )

    icon = Icon("py-logo", create_image(), "Gym Service", menu)

    server_process = multiprocessing.Process(target=start_server)
    server_process.start()

    icon.run()
    

import argparse
import logging
import sys
import threading
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openwakeword.utils
from openwakeword.model import Model
import os
import pyaudio
import numpy as np
import tts
from agent import Agent

load_dotenv(".env")

openwakeword.utils.download_models()

PORT = os.getenv("PORT", 8100)

TFLITE_MODEL_PATH = os.getenv("TFLITE_MODEL_PATH", "")
ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "")

FORMAT = pyaudio.paInt16    # 16-bit audio format
CHANNELS = 1                # Mono audio
RATE = 16000                # 16kHz is a common sample rate for wake word detection
CHUNK = 1280                # 1280 bytes correspond to 80ms of audio at 16kHz


loaded_models = Model(wakeword_models=[TFLITE_MODEL_PATH, ONNX_MODEL_PATH])
print("Models loaded successfully")

audio = pyaudio.PyAudio()

session_client_ws = None
wakeword_client_ws = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
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

app_started = False
agent = Agent()

async def send_audio_ws(websocket: WebSocket, filename: str, intent: str):
    
    await websocket.send_json({"type": "audio", "intent": intent})
    
    if filename is None:
        return
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

    global session_client_ws

    if session_client_ws is not None:
        await websocket.close(code=1000)
        return
    
    await websocket.accept()
    try:
        session_client_ws = websocket
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received message from client: {data}")
            filename = None
            intent = None

            match data.get("type"):
                case "new_command":
                    command = data.get("command", "")
                    response = await agent.parse_message(command)

                    intent = response.get("intent", {}).get("name", "")
                    confidence = response.get("intent", {}).get("confidence", 0)
                    
                    if confidence < 0.85:

                        filename = await tts.unknown()
                        print(f"Confidence too low: {confidence}")
                        agent.update_intent("unknown")
                        await send_audio_ws(websocket, filename, "unknown")
                        continue

                    print(f"Predicted intent: {intent}")

                    match intent:
                        case "greet":
                            filename = await tts.greet()

                        case "affirm":
                            if agent.get_previous_intent() == "deny":
                                filename = await tts.affirm()
                            elif agent.get_previous_intent() == "do_you_need_help":
                                filename = await tts.help_requested()
                                intent = "help_requested"
                            elif agent.get_previous_intent() == "help_requested":
                                filename = await tts.affirm()
                                intent = "show_video"
                            else:
                                filename = await tts.affirm()

                        case "deny":
                            filename = await tts.affirm()

                        case "start_training_session":
                            filename = None

                        case "next_exercise":
                            filename = await tts.next_exercise()

                        case "help":
                            if agent.get_previous_intent() == "do_you_need_help":
                                filename = await tts.help_requested()
                                intent = "help_requested"
                            else:
                                filename = await tts.help()

                        case "help_exercise":
                            if agent.get_previous_intent() == "do_you_need_help":
                                filename = await tts.help_requested()
                                intent = "help_requested"
                            else:
                                filename = await tts.help_exercise(agent._actual_exercise)

                        case "presentation":
                            filename = await tts.presentation()
                        
                        case "goodbye":
                            filename = await tts.goodbye()
                    
                    agent.update_intent(intent)
                    print(f"Sending audio file: {filename} for intent: {intent}")
                    await send_audio_ws(websocket, filename, intent)
                    continue

                case "goodbye":
                    filename = await tts.goodbye()

                case "arms_exercise":
                    intent = "ask"
                    filename = await tts.arms_exercise()
                    agent._actual_exercise = 1

                case "legs_exercise":
                    intent = "ask"
                    filename = await tts.legs_exercise()
                    agent._actual_exercise = 2

                case "walk_exercise":
                    intent = "ask"
                    filename = await tts.walk_exercise()
                    agent._actual_exercise = 3

                case "change_legs":
                    filename = await tts.change_legs()

                case "exercise_done":
                    filename = await tts.exercise_done()

                case "presentation0":
                    filename = await tts.presentation_0()

                case "presentation1":
                    filename = await tts.presentation_1()

                case "presentation2":
                    filename = await tts.presentation_2()

                case "presentation3":
                    filename = await tts.presentation_3()

                case "presentation4":
                    filename = await tts.presentation_4()

                case "presentation5":
                    intent = "ask"
                    filename = await tts.presentation_5()

                case "simple_exercise_done":
                    filename = await tts.simple_exercise_done()

                case "do_you_need_help":
                    intent = "do_you_need_help"
                    agent.update_intent("do_you_need_help")
                    filename = await tts.do_you_need_help()

                case "lets_go":
                    filename = await tts.lets_go()
                
                case _:
                    logger.warning(f"Unknown message type: {data.get('type')}")
                    filename = await tts.unknown()
            
            print(f"Sending audio file: {filename} for intent: {intent}")
            await send_audio_ws(websocket, filename, intent)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        session_client_ws = None
        await websocket.close()
        logger.info("WebSocket connection closed")

@app.websocket("/ws/wakeword")
async def websocket_wakeword(websocket: WebSocket):

    global wakeword_client_ws
    current_time = 0

    if wakeword_client_ws is not None:
        await websocket.close(code=1000)
        return
    
    await websocket.accept()

    logger.info("Wake word WebSocket connection accepted")
    await websocket.send_json({"type": "wakeword_status", "status": "ready"})

    try:
        wakeword_client_ws = websocket
        
        logger.info("Starting wake word detection loop")
        try:
            stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            logger.info("Audio stream opened for wake word detection")
        except Exception as audio_error:
            logger.error(f"Failed to open audio stream: {audio_error}")
            logger.error(f"Make sure microphone is available and not in use by another application")
            raise

        while True:
            audio_data = np.frombuffer(
                stream.read(CHUNK, exception_on_overflow=False),
                dtype=np.int16
            )

            prediction = loaded_models.predict(audio_data)
            
            ola_gym_confidence = prediction.get("ola_jim", 0.0)

            if ola_gym_confidence > 0:
                print(f"Wake word confidence: {ola_gym_confidence:.4f}", end="\r")

            if ola_gym_confidence > 0.4 and (time.time() - current_time) > 2:
                logger.info(f"Wake word detected with confidence {ola_gym_confidence:.4f}")
                try:
                    await websocket.send_json({"type": "wakeword_detected", "confidence": float(ola_gym_confidence)})
                except Exception as send_error:
                    logger.error(f"Failed to send wake word detection message: {send_error}")
                    break
                current_time = time.time()

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        wakeword_client_ws = None
        stream.stop_stream()
        stream.close()
        await websocket.close()
        logger.info("WebSocket connection closed")

def start_server():
    global app_started
    
    parser = argparse.ArgumentParser(description="Gym Service for managing workout sessions")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--log-level", type=str, default="info", choices=["debug", "info", "warning", "error", "critical"], help="Set the logging level")

    args = parser.parse_args()

    logger.info(f"Starting Gym Service with log level {args.log_level}")

    app_started = True

    uvicorn.run(
        "app:app" if args.reload else app,
        host="localhost",
        port=8100,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True,
    )

def update_icon(icon):
    while True:
        time.sleep(1)
        if icon and icon.visible:
            icon.icon = create_image()
            icon.update_menu()

if __name__ == "__main__":

    server_thread = None

    def create_image():
        image = Image.open("images/py-logo.png")
        return image

    def quit_app(icon):
        icon.stop()
        sys.exit(0)

    def get_status_text(icon):
        return "Ready" if app_started else "Loading..."

    def create_menu():

        menu = Menu(
            MenuItem(
                text=get_status_text,
                action=None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem("Sair", quit_app),
        )

        return menu
    
    menu = create_menu()

    icon = Icon("py-logo", create_image(), "Gym Service", menu)

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    icon_thread = threading.Thread(target=update_icon, args=(icon,), daemon=True)
    icon_thread.start()

    icon.run()
    

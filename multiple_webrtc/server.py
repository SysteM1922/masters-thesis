import asyncio
from dotenv import load_dotenv
import logging

import os
from websockets.asyncio.server import serve
import websockets
import multiprocessing

load_dotenv(override=True)

# Global variables
server_ip = None
server_port = None

stun_servers = []
turn_servers = []
turn_username = None
turn_password = None

server_socket = None
client_sockets = {}
client_ids = set()

# Function to handle .env file loading and environment variable setting
def handle_dotenv():
    global server_ip, server_port
    server_ip = os.getenv("SERVER_IP")
    server_port = int(os.getenv("SERVER_PORT"))
    print(f"Server IP: {server_ip}, Server Port: {server_port}")
    
    if server_ip is None or server_port is None:
        raise ValueError("SERVER_IP and SERVER_PORT must be set in the .env file.")

    global stun_servers, turn_servers, turn_username, turn_password
    stun_servers = os.getenv("STUN_SERVERS").split(",") if os.getenv("STUN_SERVERS") else []
    turn_servers = os.getenv("TURN_SERVERS").split(",") if os.getenv("TURN_SERVERS") else []
    turn_username = os.getenv("TURN_USERNAME", None)
    turn_password = os.getenv("TURN_PASSWORD", None)

    logging.info(f"Environment variables loaded")

def worker_process(conn, client_id):
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
    import json
    
    pc = RTCPeerConnection({
        "iceServers": [
            {"urls": stun_servers},
            {"urls": turn_servers, "username": turn_username, "credential": turn_password}
        ]
    })
    
    print("Worker process started for client:", client_id)

async def handler(websocket):
    async for message in websocket:
        logging.info(f"Received message: {message}")

async def run_server():
    async with serve(handler, server_ip, server_port) as server:
        await server.serve_forever()
        
if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Starting WebRTC server...")
        handle_dotenv()
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logging.info("Server stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Server shutting down...")


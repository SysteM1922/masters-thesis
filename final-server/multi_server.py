import subprocess
import os
from dotenv import load_dotenv
import asyncio
import websockets
import json

load_dotenv(".env")

ids_pool = []

SIGNALING_IP = os.getenv("SIGNALING_SERVER_HOST")
SIGNALING_PORT = os.getenv("SIGNALING_SERVER_PORT")
SERVER_ID = os.getenv("SERVER_ID")

actual_id = 50000

def summon_processing_unit():
    global actual_id
    while actual_id in ids_pool:
        actual_id += 1
    ids_pool.append(actual_id)

    subprocess.Popen(
        ["python", "processing_unit.py", "--host", SIGNALING_IP, "--port", SIGNALING_PORT, "--id", SERVER_ID + "-" + str(actual_id)]
    )

def processing_unit_off(unit_id):
    global ids_pool, actual_id
    id = unit_id.split("-")[-1]
    ids_pool.remove(int(id))
    actual_id = int(id)

async def main():
    global actual_id

    async with websockets.connect(f"ws://{SIGNALING_IP}:{SIGNALING_PORT}/ws/server") as ws:
        
        await ws.send(
            json.dumps({"type": "register", "server_id": SERVER_ID})
        )

        async for message in ws:
            data = json.loads(message)
            print("Received message:", data)

            match data.get("type"):

                case "register":
                    if data.get("registered"):
                        print("Server registered successfully")
                    else:
                        print("Server registration failed")
                        return

                case "request_processing_unit":
                    summon_processing_unit()
                    print(f"Summoned Processing Unit: {actual_id}")

                case "unit_disconnect":
                    unit_id = data.get("unit_id")
                    processing_unit_off(unit_id)

                case "signaling_disconnect":
                    print("Signaling server disconnected")
                    break

                case _:
                    print(f"Unknown message type: {data.get('type')}")

if __name__ == "__main__":
    asyncio.run(main())


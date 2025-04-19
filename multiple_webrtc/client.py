from websockets.asyncio.client import connect
import asyncio

async def run_client():
    uri = "ws://localhost:8765"  # Replace with server URI
    async with connect(uri) as websocket:
        print("Connected to server.")
        while True:
            await websocket.send("teste")
            print("Message sent: teste")
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        print("Starting client...")
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("Client stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Client closed.")
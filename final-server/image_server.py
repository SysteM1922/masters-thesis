import json
from aiortc import MediaStreamError, RTCConfiguration, RTCIceServer, RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
import av
import mediapipe as mp
from mediapipe.tasks.python import vision
import time
import asyncio
import threading
from dataclasses import asdict
import sys
import websockets
import os
from dotenv import load_dotenv

from api_interface import TestsAPI
from utils import get_time_offset

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv("../.env")

SIGNALING_IP = os.getenv("SIGNALING_SERVER_HOST")
SIGNALING_PORT = os.getenv("SIGNALING_SERVER_PORT")

test_id = None

last_frame = None
data_channel = None
media_track = None

stop_pose_thread = threading.Event()
process_frame_flag = threading.Event()

arrival_times = []
start_process_times = []
end_process_times = []
send_times = []

base_options = mp.tasks.BaseOptions(
    model_asset_path="../models/pose_landmarker_lite.task", # Path to the model file
    delegate=mp.tasks.BaseOptions.Delegate.CPU, # Use GPU if available (only on Linux)
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

detector = vision.PoseLandmarker.create_from_options(options)

class WebsocketSignalingServer:
    def __init__(self, host, port, id):
        self.host = host
        self.port = port
        self.websocket = None
        self.id = id
        self.client_id = None

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://{self.host}:{self.port}/ws/server")
        await self.websocket.send(json.dumps({
            "type": "register",
            "server_id": self.id,
        }))

    async def send(self, obj):
        if hasattr(obj, "sdp"):
            message = {"type": obj.type, "sdp": obj.sdp}
        else:
            message = obj

        try:
            await self.websocket.send(json.dumps(message))
            print(f"Sent message: {obj.type if hasattr(obj, 'type') else message.get('type', 'unknown')}")
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
        
    async def send_answer(self, pc: RTCPeerConnection, client_id: str):
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await self.send({
            "type": "answer",
            "sdp": pc.localDescription.sdp,
            "client_id": client_id
        })
        print("Answer sent to signaling server")

    async def send_ice_candidate(self, candidate):
        if candidate is None:
            return
        
        message = {
            "type": "ice_candidate",
            "candidate": {
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex
            },
            "client_id": self.client_id
        }
        await self.send(message)
        print("ICE candidate sent to signaling server")

    async def accept_client(self, client_id):
        self.client_id = client_id
        await self.send({
            "type": "accept_connection",
            "client_id": client_id,
            "message": "Client connection accepted."
        })

    async def receive_offer(self, pc: RTCPeerConnection, message: dict):
        obj = RTCSessionDescription(
            sdp=message.get("sdp"),
            type=message.get("type")
        )
        await pc.setRemoteDescription(obj)

    async def handle_messages(self, pc: RTCPeerConnection):
        errors = 0
        while True:
            try:
                message = await self.websocket.recv()
                message = json.loads(message)

                match message.get("type", None):
                    case "register":
                        if message.get("registered"):
                            print(f"Server {self.id} registered successfully")
                        else:
                            print(f"Server {self.id} registration failed")
                            return

                    case "connect":
                        print(f"Client {message.get('client_id')} wants to connect")
                        await self.accept_client(message.get("client_id"))

                    case "offer":
                        print("Received offer from client")
                        await self.receive_offer(pc, message)
                        await self.send_answer(pc, message.get("client_id"))

                    case "ice_candidate":
                        print("Received ICE candidate from client")
                        candidate = message.get("candidate")
                        if candidate:
                            await pc.addIceCandidate(RTCIceCandidate(
                                component=candidate.get("component"),
                                foundation=candidate.get("foundation"),
                                ip=candidate.get("ip"),
                                port=candidate.get("port"),
                                priority=candidate.get("priority"),
                                protocol=candidate.get("protocol"),
                                type=candidate.get("type"),
                                relatedAddress=candidate.get("relatedAddress", None),
                                relatedPort=candidate.get("relatedPort", None),
                                sdpMid=candidate.get("sdpMid", None),
                                sdpMLineIndex=candidate.get("sdpMLineIndex", None),
                                tcpType=candidate.get("tcpType", None),
                            ))
                        else:
                            print("Received empty ICE candidate, ignoring")

                    case "signaling_disconnect":
                        print("Signaling server disconnected")
                        break

                    case "disconnect":
                        print(f"Client disconnected: {message.get('client_id')}")
                        break

                    case "error":
                        print(f"Error from server: {message.get('message', 'Unknown error')}")
                        errors += 1
                        if errors > 5:
                            print("Too many errors, closing connection")
                            break

                    case _:
                        print(f"Received message: {message}")
            
            except websockets.ConnectionClosed:
                break

            except Exception as e:
                print(f"Error receiving message: {e}")
        

    async def close(self):
        if self.websocket is not None:
            try:
                await self.websocket.close()
                print("WebSocket connection closed")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")
    
async def handle_results(results, frame_pts):
    if results.pose_landmarks:
        landmarkslist = [asdict(landmark) for landmark in results.pose_landmarks[0]]
    else:
        landmarkslist = []
    data = json.dumps({
        "landmarks": landmarkslist,
        "frame_count": frame_pts
    })
    
    try:
        # Check if data_channel exists and is open before sending
        if data_channel and data_channel.readyState == "open":
            send_times.append((frame_pts, time.time()))
            data_channel.send(data)
    except Exception as e:
        print(f"Error sending data: {e}")

def process_frame():
    while not stop_pose_thread.is_set():
        process_frame_flag.wait()  # Wait until a frame is available
        last_frame_pts = last_frame.pts
        start_process_times.append((last_frame_pts, time.time()))
        try:
            image = last_frame.to_ndarray(format="bgr24")
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            results = detector.detect(mp_image)
            end_process_times.append((last_frame_pts, time.time()))
            _ = asyncio.run(handle_results(results, last_frame_pts))
        except Exception as e:
            print("Error processing frame:", e)
            continue
        process_frame_flag.clear()  # Clear the flag to wait for the next frame

async def handle_track(track):
    global last_frame, arrival_times, process_frame_flag, stop_pose_thread
    threading.Thread(target=process_frame, daemon=True).start()

    while not stop_pose_thread.is_set():
        try:
            last_frame = await track.recv()
            # print frame resolution
            print(f"Received frame: {last_frame.width}x{last_frame.height}, pts: {last_frame.pts}")
            arrival_time = time.time()
            if last_frame is not None:
                arrival_times.append((last_frame.pts, arrival_time))
                process_frame_flag.set()
        except MediaStreamError as e:
            print("MediaStreamError:", e)
            break
        except Exception as e:
            print("Error receiving track:", e)

async def run(host, port):
    signaling = WebsocketSignalingServer(host, port, "server_id")
    pc_config = RTCConfiguration(
        iceServers=[
            RTCIceServer(
                urls="stun:192.168.1.100:3478",
                username="gymuser",
                credential="gym456"
            ),
            RTCIceServer(
                urls="turn:192.168.1.100:3478",
                username="gymuser",
                credential="gym456"
            ),
            RTCIceServer(
                urls="stun:stun.l.google.com:19302",
            )
        ],
    )
    pc = RTCPeerConnection(pc_config)

    try:
        await signaling.connect()

        # Reset global state for new connection
        stop_pose_thread.clear()
        data_channel = None

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print("ICE candidate received:", candidate)
            await signaling.send_ice_candidate(candidate)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print("ICE connection state is", pc.iceConnectionState)


        @pc.on("datachannel")
        def on_datachannel(channel):
            print("Data channel opened")
            global data_channel
            data_channel = channel

            @channel.on("close")
            def on_close():
                print("Data channel closed")
                global data_channel
                data_channel = None

            @channel.on("stop")
            def on_stop():
                print("Data channel stopped")
                global data_channel
                data_channel = None
                channel.close()

            @channel.on("message")
            def on_message(message):
                global test_id
                print("Message received:", message)
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        if "test_id" in data:
                            test_id = data["test_id"]
                    except json.JSONDecodeError:
                        print("Received non-JSON message:", message)

        @pc.on("track")
        def on_track(track):
            global media_track
            print("Track received")
            media_track = track

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is", pc.connectionState)
            if pc.connectionState == "connected":
                print("WebRTC connected")
                asyncio.create_task(handle_track(media_track))
            elif pc.connectionState in ["closed", "failed", "disconnected"]:
                print("WebRTC connection ended:", pc.connectionState)
                raise MediaStreamError("WebRTC connection ended")

        await signaling.handle_messages(pc)
    
    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        print("Closing connection...")
        
        await signaling.close()
        await pc.close()
        stop_pose_thread.set()


if __name__ == "__main__":
    
    time_offset = 0

    try:
        asyncio.run(run(SIGNALING_IP, SIGNALING_PORT))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        detector.close()
        #exit(0)

        print("Adding measurements to the test. Please wait...")

        TestsAPI.add_measurement_bulk(
            results_list= [
                {
                    "point": "{\"point_b\": " + str(arrival_time[0]) + "}",
                    "timestamp": arrival_time[1] + time_offset
                } for arrival_time in arrival_times
            ],
            test_id=test_id,
        )

        TestsAPI.add_measurement_bulk(
            results_list= [
                {
                    "point": "{\"point_c\": " + str(start_process_time[0]) + "}",
                    "timestamp": start_process_time[1] + time_offset
                } for start_process_time in start_process_times
            ],
            test_id=test_id,
        )

        TestsAPI.add_measurement_bulk(
            results_list= [
                {
                    "point": "{\"point_d\": " + str(end_process_time[0]) + "}",
                    "timestamp": end_process_time[1] + time_offset
                } for end_process_time in end_process_times
            ],
            test_id=test_id,
        )

        TestsAPI.add_measurement_bulk(
            results_list= [
                {
                    "point": "{\"point_e\": " + str(send_time[0]) + "}",
                    "timestamp": send_time[1] + time_offset
                } for send_time in send_times
            ],
            test_id=test_id,
        )
            
        print("Test completed and measurements added.")
        print(f"Test ID: {test_id}")
        exit(0)
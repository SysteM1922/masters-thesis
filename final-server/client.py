import asyncio
import fractions
import os
import threading
import websockets
import cv2
import json
import time
import utils
import sys
import subprocess
from utils import get_time_offset
from api_interface import TestsAPI
from copy import deepcopy
from aiortc import RTCConfiguration, RTCIceCandidate, RTCIceServer, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from dotenv import load_dotenv
import logging

load_dotenv(".env")

logging.basicConfig(
    filename='client.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

SIGNALING_IP = os.getenv("SIGNALING_SERVER_HOST")
SIGNALING_PORT = os.getenv("SIGNALING_SERVER_PORT")

TURN_SERVER_HOST = os.getenv("TURN_SERVER_HOST")
TURN_SERVER_PORT = os.getenv("TURN_SERVER_PORT")
TURN_SERVER_USERNAME = os.getenv("TURN_SERVER_USERNAME")
TURN_SERVER_CREDENTIAL = os.getenv("TURN_SERVER_CREDENTIAL")

FPS = 30

test_id = None
test_type = "gym"
houseID = "house01"
division = "sala"
id = "client_id"

send_times = []
arrival_times = []

resume_display = threading.Event()
stop_display = threading.Event()

arms_exercise_reps = 0

class WebsocketSignalingClient:
    def __init__(self, host, port, id):
        self.host = host
        self.port = port
        self.websocket = None
        self.id = id

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://{self.host}:{self.port}/ws")
        print(f"Connected to signaling server at {self.host}:{self.port}")
        await self.websocket.send(json.dumps({
            "type": "connect",
            "client_id": self.id,
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
        
    async def send_offer(self, pc: RTCPeerConnection):
        """Send an offer to the signaling server."""
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await self.send(pc.localDescription)
        print("Offer sent to signaling server")

    async def receive_answer(self, pc: RTCPeerConnection, message: dict):
        obj = RTCSessionDescription(
            sdp=message.get("sdp"),
            type=message.get("type")
        )
        await pc.setRemoteDescription(obj)

    async def send_ice_candidate(self, candidate):
        if candidate is None:
            return
        
        message = {
            "type": "ice_candidate",
            "candidate": {
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex
            }
        }
        await self.send(message)
        print("ICE candidate sent to signaling server")

    async def handle_messages(self, pc: RTCPeerConnection):
        errors = 0
        try:
            while True:
                message = await self.websocket.recv()
                message = json.loads(message)
    
                match message.get("type", None):
                    case "register":
                        if message.get("registered"):
                            print(f"Client {self.id} registered successfully")
                        else:
                            print(f"Failed to register client {self.id}: {message.get('message', 'Unknown error')}")
                            break
                        
                    case "connecting":
                        print(f"Connecting to server: {message.get('unit_id')}")
    
                    case "accepted_connection":
                        print(f"Connection accepted by server: {message.get('unit_id')}")
                        await self.send_offer(pc)
    
                    case "answer":
                        print("Received answer")
                        await self.receive_answer(pc, message)

                    case "ice_candidate":
                        print("Received ICE candidate from client")
                        candidate = message.get("candidate")
                        if candidate:
                            pc.addIceCandidate(RTCIceCandidate(
                                candidate=candidate.get("candidate"),
                                sdpMid=candidate.get("sdpMid"),
                                sdpMLineIndex=candidate.get("sdpMLineIndex")
                            ))
                        else:
                            print("Received empty ICE candidate, ignoring")

                    case "signaling_disconnect":
                        print("Signaling server disconnected")
                        break

                    case "disconnect":
                        print(f"Server disconnected: {message.get('unit_id')}")
                        break
    
                    case "error":
                        print(f"Error from server: {message.get('message', 'Unknown error')}")
                        errors += 1
                        if errors > 5:
                            print("Too many errors, closing connection")
                            break
                        
                    case _:
                        print(f"Received message: {message}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
        finally:
            await self.close()

        
    async def close(self):
        if self.websocket is not None:
            try:
                await self.websocket.close()
                print("WebSocket connection closed")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None

def display_image():
    try:
        while not stop_display.is_set():
            resume_display.wait()  # Wait until the display is resumed
            #cv2.putText(actual_frame, f"Leg Repetitions: {leg_exercise_reps}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(actual_frame, f"Repetitions: {arms_exercise_reps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            #cv2.putText(actual_frame, f"Steps: {correct_steps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.imwrite("output_client.jpg", actual_frame) # if Linux is not displaying the image, save it to a file and comment the imshow line
            #cv2.imshow("MediaPipe Pose", actual_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_display.set()
            
    except Exception as e:
        print(f"Error in display thread: {e}")

class VideoTrack(VideoStreamTrack):
    def __init__(self, path):
        super().__init__()
        width = 1280
        height = 720
        cap = None
        if sys.platform == "linux":
            cap = cv2.VideoCapture(path, cv2.CAP_V4L2)
        elif sys.platform == "win32":
            cap = cv2.VideoCapture(path, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(path, cv2.CAP_ANY)
        #self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, FPS)
        self.cap = cap
        self.frame_count_division_factor = int(90000 / FPS)
        self.frame_count = -1
        self.frames = []
        self.last_frame_count = -1
        #self.fps = 0
        #self.start_time = time.time()

    async def recv(self):
        global send_times
        self.frame_count += 1
        ret, frame = self.cap.read()

        if not ret:
            print("Failed to read frame from camera")
            return None

        frame = cv2.flip(frame, 1)
        self.frames.append(tuple((frame, self.frame_count)))
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, FPS)
        #send_times.append((self.frame_count, time.time()))
        logging.debug(f"Sent frame {self.frame_count}")
        return video_frame
    
    async def process_frame(self, message):
        #arrival_time = time.time()
        global arms_exercise_reps, arrival_times, actual_frame, resume_display, angle
        #self.fps+=1
        #if (time.time() - self.start_time > 1):
            #print(self.fps, "fps")
            #self.fps = 0
            #self.start_time = time.time()

        data = json.loads(message)
        frame_count = data.get("frame_count", -2) + 1
        frame_count //= self.frame_count_division_factor
        #arrival_times.append((frame_count, arrival_time))
        if frame_count == -1 and frame_count > self.last_frame_count:
            return
        while self.frames:
            frame, pts = self.frames.pop(0)
            if pts == frame_count:
                logging.debug(f"Received frame {frame_count}")
                landmarks = data.get("landmarks", None)
                if landmarks:
                    styled_connections = data.get("style", None)
                    #styled_connections = leg_exercise(landmarks, right_leg=True)
                    #styled_connections = walk_exercise(landmarks)
                    if styled_connections:
                        utils.draw_from_json(
                            image=frame,
                            landmark_json=landmarks,
                            connections_style=styled_connections,
                        )
                    else:
                        utils.draw_from_json(
                            image=frame,
                            landmark_json=landmarks,
                        )

                    new_rep = data.get("new_rep", False)
                    if new_rep:
                        arms_exercise_reps += 1

                actual_frame = frame
                self.last_frame_count = frame_count
                resume_display.set()  # Resume the display thread
                break
    
async def run(ip_address, port):
    signaling = WebsocketSignalingClient(ip_address, port, id)
    pc_config = RTCConfiguration(
        iceServers=[
            RTCIceServer(
                urls=f"turn:{TURN_SERVER_HOST}:{TURN_SERVER_PORT}",
                username=TURN_SERVER_USERNAME,
                credential=TURN_SERVER_CREDENTIAL
            ),
            RTCIceServer(
                urls="stun:stun1.l.google.com:3478"
            )
        ],
    )

    pc = RTCPeerConnection(pc_config)
    video_track = VideoTrack(0)
    pc.addTrack(video_track)
    print("Added video track")

    def create_test(data_channel):
        global test_id, houseID, division, test_type, time_offset
        test_id = TestsAPI.create_test(
            test_type=test_type,
            house_id=houseID,
            division=division
        )

        data_channel.send(json.dumps({
            "test_id": test_id
        }))

    def start_display_thread():
        process_thread = threading.Thread(target=display_image)
        process_thread.daemon = True
        process_thread.start()

    try:
        await signaling.connect()

        data_channel = pc.createDataChannel("data")

        @data_channel.on("open")
        def on_open():
            print("Data channel is open")
            start_display_thread()
            create_test(data_channel)

        @data_channel.on("message")
        def on_message(message):
            asyncio.create_task(video_track.process_frame(message))

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is", pc.connectionState)
            if pc.connectionState == "connected":
                print("WebRTC connected")
            elif pc.connectionState  in ["closed", "failed", "disconnected"]:
                print("WebRTC connection closed or failed")
                stop_display.set()

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            print("ICE candidate received:", candidate)
            await signaling.send_ice_candidate(candidate)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print("ICE connection state is", pc.iceConnectionState)

        await signaling.handle_messages(pc)
    
    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("Keyboard interrupt received, closing connection")
        stop_display.set()
    
    finally:
        print("Closing connection")
        
        await signaling.close()
        await pc.close()

        resume_display.set()  # Ensure display thread can exit

        cv2.destroyAllWindows()

if __name__ == "__main__":

    time_offset = 0

    """if sys.platform == "win32":
        try:
            subprocess.run(["python", "../clock_sync/client.py", "--server_ip", SERVER_IP], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Error running clock sync client: {e}")
            sys.exit(1)
    else:
        try:
            subprocess.run(["python3", "../clock_sync/client.py", "--server_ip", SERVER_IP], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Error running clock sync client: {e}")
            sys.exit(1)"""

    """with open("offset.txt", "r") as f:
        try:
            time_offset = float(f.readline().strip())
            print(f"Time offset loaded: {time_offset} seconds")
        except ValueError as e:
            print(f"Error reading time offset: {e}")
            sys.exit(1)"""

    try:
        asyncio.run(run(SIGNALING_IP, SIGNALING_PORT))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        exit(0)

        print("Adding measurements to the test. Please wait...")

        TestsAPI.update_test(
            test_id=test_id,
            start_time=time.time() + time_offset,
            notes="{\"offset\": " + str(time_offset) + ", \"fps\": " + str(FPS) + "}"
        )

        for arrival_time in arrival_times:
            TestsAPI.add_measurement_bulk(
                results_list= [
                    {
                        "point": "{\"point_f\": " + str(arrival_time[0]) + "}",
                        "timestamp": arrival_time[1] + time_offset
                    },
                ],
                test_id=test_id,
            )
            TestsAPI.add_measurement_bulk(
                results_list= [
                    {
                        "point": "{\"point_a\": " + str(arrival_time[0]) + "}",
                        "timestamp": send_times[arrival_time[0]][1] + time_offset
                    },
                ],
                test_id=test_id,
            )

        print("Test completed and measurements added.")
        print(f"Test ID: {test_id}")
        exit(0)

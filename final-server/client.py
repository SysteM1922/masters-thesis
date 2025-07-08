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
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from dotenv import load_dotenv

load_dotenv("../.env")

SIGNALING_IP = os.getenv("SIGNALING_SERVER_HOST")
SIGNALING_PORT = os.getenv("SIGNALING_SERVER_PORT")

FPS = 30

test_id = None
test_type = "gym"
houseID = "house01"
division = "sala"
id = "client_id"

send_times = []
arrival_times = []

actual_frame = None
right_arm_state_repetition = 0
right_arm_state = None

resume_display = threading.Event()
stop_display = threading.Event()

def right_arm_angle(right_shoulder: dict, right_elbow: dict, right_wrist: dict):
    global right_arm_state_repetition, right_arm_state
    right_arm = None
    if right_shoulder['visibility'] > 0.5 and right_elbow['visibility'] > 0.5 and right_wrist['visibility'] > 0.5:
        new_right_shoulder = deepcopy(right_shoulder)
        new_right_shoulder['x'] = -right_shoulder['x']
        new_right_wrist = deepcopy(right_wrist)
        new_right_wrist['x'] = -right_wrist['x']
        right_arm_angle = utils.get_angle_2_points_x_axis(new_right_shoulder, new_right_wrist)
        right_elbow_angle = utils.get_angle_3_points(right_shoulder, right_elbow, right_wrist)

        if right_arm_angle < 10 and right_elbow_angle > 140:
            right_arm = True
        elif right_arm_angle > 60:
            right_arm = None
        else:
            right_arm = False

    if right_arm != right_arm_state:
        right_arm_state_repetition -= 1

        if right_arm == False and right_arm_state_repetition < -20:
            right_arm_state_repetition = 0
            right_arm_state = right_arm
        elif right_arm_state_repetition < 0:
            right_arm_state_repetition = 0
            right_arm_state = right_arm

    else: 
        if right_arm_state_repetition < 10:
            right_arm_state_repetition += 1

    return right_arm_state

left_arm_state_repetition = 0
left_arm_state = None

def left_arm_angle(left_shoulder, left_elbow, left_wrist):
    global left_arm_state_repetition, left_arm_state
    left_arm = None

    if left_shoulder['visibility'] > 0.5 and left_elbow['visibility'] > 0.5 and left_wrist['visibility'] > 0.5:
        left_arm_angle = utils.get_angle_2_points_x_axis(left_shoulder, left_wrist)
        left_elbow_angle = utils.get_angle_3_points(left_shoulder, left_elbow, left_wrist)

        if left_arm_angle < 10 and left_elbow_angle > 140:
            left_arm = True
        elif left_arm_angle > 60:
            left_arm = None
        else:
            left_arm = False

    if left_arm != left_arm_state:
        left_arm_state_repetition -= 1

        if left_arm == False and left_arm_state_repetition < -20:
            left_arm_state_repetition = 0
            left_arm_state = left_arm
        elif left_arm_state_repetition < 0:
            left_arm_state_repetition = 0
            left_arm_state = left_arm

    else:   
        if left_arm_state_repetition < 10:
            left_arm_state_repetition += 1

    return left_arm_state
    

def arms_angle(right_shoulder, left_shoulder, right_elbow, left_elbow, right_wrist, left_wrist):
    right_arm_state = right_arm_angle(right_shoulder, right_elbow, right_wrist) 
    left_arm_state = left_arm_angle(left_shoulder, left_elbow, left_wrist)

    return right_arm_state, left_arm_state

spine_state_repetition = 0
spine_state = None

def spine_straight(right_shoulder: dict, left_shoulder: dict, right_hip: dict, left_hip: dict):
    global spine_state_repetition, spine_state
    spine = None
    if right_shoulder['visibility'] > 0.5 and left_shoulder['visibility'] > 0.5 and right_hip['visibility'] > 0.5 and left_hip['visibility'] > 0.5:
        angle_shoulder_hip = utils.get_angle_4_points(right_shoulder, left_shoulder, right_hip, left_hip)
        angle_left_shoulder_hip = abs(utils.get_angle_3_points(left_shoulder, right_shoulder, right_hip) % 90)
        angle_right_shoulder_hip = abs(utils.get_angle_3_points(right_shoulder, left_shoulder, left_hip) % 90)
        if angle_shoulder_hip < 7 and angle_left_shoulder_hip - angle_right_shoulder_hip < 15:
            spine = True
        else:
            spine = False
    
    if spine != spine_state:
        spine_state_repetition -= 1

        if spine_state_repetition < 0:
            spine_state_repetition = 0
            spine_state = spine

    else:
        if spine_state_repetition < 10:
            spine_state_repetition += 1

    return spine_state

arms_exercise_state_repetition = 0
arms_exercise_state = None
old_arms_exercise_state = None
arms_exercise_reps = 0

def arms_exercise(landmarks):
    global arms_exercise_state_repetition, arms_exercise_state, arms_exercise_reps, old_arms_exercise_state

    spine_state = spine_straight(
        landmarks[12],
        landmarks[11],
        landmarks[24],
        landmarks[23]
    )

    right_arm_state, left_arm_state = arms_angle(
        landmarks[12],
        landmarks[11],
        landmarks[14],
        landmarks[13],
        landmarks[16],
        landmarks[15]
    )

    arms_exercise = None

    if right_arm_state is None and left_arm_state is None:
        arms_exercise = None

    elif right_arm_state and left_arm_state and spine_state:
        arms_exercise = True

    elif not right_arm_state or not left_arm_state or not spine_state:
        arms_exercise = False

    if arms_exercise != arms_exercise_state:
        arms_exercise_state_repetition -= 1

        if arms_exercise_state_repetition < 0:
            arms_exercise_state_repetition = 0
            if arms_exercise == True and (old_arms_exercise_state is None or arms_exercise_state is None):
                arms_exercise_reps += 1
                
            old_arms_exercise_state = arms_exercise_state
            arms_exercise_state = arms_exercise
    else:
        if arms_exercise_state_repetition < 5:
            arms_exercise_state_repetition += 1

    right_arm_style = utils.GREEN_STYLE if right_arm_state else utils.RED_STYLE
    left_arm_style = utils.GREEN_STYLE if left_arm_state else utils.RED_STYLE
    torso_style = utils.GREEN_STYLE if spine_state else utils.RED_STYLE
    
    styled_connections = utils.get_colored_style(
        right_arm= None if arms_exercise is None else right_arm_style,
        left_arm= None if arms_exercise is None is None else left_arm_style,
        torso= None if arms_exercise is None else torso_style,
    )
    return styled_connections

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
                        print(f"Connecting to server: {message.get('server_id')}")
    
                    case "accepted_connection":
                        print(f"Connection accepted by server: {message.get('server_id')}")
                        await self.send_offer(pc)
    
                    case "answer":
                        print("Received answer")
                        await self.receive_answer(pc, message)

                    case "signaling_disconnect":
                        print("Signaling server disconnected")
                        break

                    case "disconnect":
                        print(f"Server disconnected: {message.get('server_id')}")
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
            cv2.putText(actual_frame, f"Repetitions: {arms_exercise_reps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("MediaPipe Pose", actual_frame)
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
        send_times.append((self.frame_count, time.time()))
        return video_frame
    
    async def process_frame(self, message):
        arrival_time = time.time()
        global arms_exercise_reps, arrival_times, actual_frame, resume_display
        #self.fps+=1
        #if (time.time() - self.start_time > 1):
            #print(self.fps, "fps")
            #self.fps = 0
            #self.start_time = time.time()

        data = json.loads(message)
        frame_count = data.get("frame_count", -2) + 1
        frame_count //= self.frame_count_division_factor
        arrival_times.append((frame_count, arrival_time))
        if frame_count == -1 and frame_count > self.last_frame_count:
            return
        while self.frames:
            frame, pts = self.frames.pop(0)
            if pts == frame_count:
                landmarks = data.get("landmarks", None)
                if landmarks:
                    styled_connections = arms_exercise(deepcopy(landmarks))
                    if styled_connections:
                        utils.new_draw_landmarks(
                            image=frame,
                            landmark_list=landmarks,
                            connections=utils._POSE_CONNECTIONS,
                            connection_drawing_spec=styled_connections,
                        )
                    else:
                        utils.new_draw_landmarks(
                            image=frame,
                            landmark_list=landmarks,
                            connections=utils._POSE_CONNECTIONS,
                        )
                actual_frame = frame
                self.last_frame_count = frame_count
                resume_display.set()  # Resume the display thread
                break
    
async def run(ip_address, port):
    signaling = WebsocketSignalingClient(ip_address, port, id)
    pc_config = {
    
    }
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

        await signaling.handle_messages(pc)

        """# Run until the connection is closed or user interrupts
        while not stop_display.is_set():
            await asyncio.sleep(5)"""
    
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
        #exit(0)

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

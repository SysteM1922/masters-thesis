import asyncio
import fractions
import threading
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
# linux conflit cv2 and av/aiortc

SERVER_IP = "100.123.205.104" # Tailscale IP
#SERVER_IP = "localhost" # Local testing
#SERVER_IP = "10.255.40.73" # GYM VM
#SERVER_IP = "10.255.32.55" # GPU VM
#SERVER_IP = "192.168.1.207"
SERVER_PORT = 8000

FPS = 30

test_id = None
test_type = "gym"
houseID = "house01"
division = "sala"

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

class TcpSocketSignalingClient:
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.ip_address, self.port
        )
        print(f"Connected to signaling server at {self.ip_address}:{self.port}")

    async def send(self, obj):
        if self.writer is None:
            raise ConnectionError("Not connected to signaling server")
        
        if hasattr(obj, "sdp"):
            message = {"type": obj.type, "sdp": obj.sdp}
        else:
            message = obj

        data = json.dumps(message).encode() + b'\n'
        self.writer.write(data)
        await self.writer.drain()

    async def receive(self):
        if self.reader is None:
            return None
        
        try:
            data = await self.reader.readline()
            if not data:
                return None
            
            message = json.loads(data.decode().strip())
            if "type" in message and "sdp" in message:
                return RTCSessionDescription(sdp=message["sdp"], type=message["type"])
            else:
                return message
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
        
    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("Connection closed")
        else:
            print("No connection to close")

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
    signaling = TcpSocketSignalingClient(ip_address, port)
    pc = RTCPeerConnection()
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
        print("Connecting to server")

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

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await signaling.send(pc.localDescription)

        while True:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                if obj.type == "answer":
                    await pc.setRemoteDescription(obj)
                    print("Received answer")
                    break
                else:
                    print(f"Unexpected SDP type: {obj.type}")
            elif obj is None:
                print("Connection closed by server")
                return
            else:
                print(f"Received unexpected object: {obj}")

        # Run until the connection is closed or user interrupts
        while not stop_display.is_set():
            await asyncio.sleep(5)
    
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
        asyncio.run(run(SERVER_IP, SERVER_PORT))
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

import asyncio
import fractions
import pickle
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import cv2
import time
import utils


send_times = []
arrival_times = []

class Joint:
    def __init__(self, joint):
        self.x = joint.x
        self.y = joint.y

right_arm_state_repetition = 0
right_arm_state = None

def right_arm_angle(right_shoulder, right_elbow, right_wrist):
    global right_arm_state_repetition, right_arm_state
    right_arm = None
    if right_shoulder.visibility > 0.5 and right_elbow.visibility > 0.5 and right_wrist.visibility > 0.5:
        new_right_shoulder = Joint(right_shoulder)
        new_right_shoulder.x = -right_shoulder.x
        new_right_wrist = Joint(right_wrist)
        new_right_wrist.x = -right_wrist.x
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

    if left_shoulder.visibility > 0.5 and left_elbow.visibility > 0.5 and left_wrist.visibility > 0.5:
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

def spine_straight(right_shoulder, left_shoulder, right_hip, left_hip):
    global spine_state_repetition, spine_state
    spine = None
    if right_shoulder.visibility > 0.5 and left_shoulder.visibility > 0.5 and right_hip.visibility > 0.5 and left_hip.visibility > 0.5:
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
        landmarks.landmark[12],
        landmarks.landmark[11],
        landmarks.landmark[24],
        landmarks.landmark[23]
    )

    right_arm_state, left_arm_state = arms_angle(
        landmarks.landmark[12],
        landmarks.landmark[11],
        landmarks.landmark[14],
        landmarks.landmark[13],
        landmarks.landmark[16],
        landmarks.landmark[15]
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

class VideoTrack(VideoStreamTrack):
    def __init__(self, path):
        super().__init__()
        width = 1280
        height = 720
        self.cap = cv2.VideoCapture(path)
        #self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.frame_count = 0
        self.frames = []
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
        self.frames.append(tuple((frame, self.frame_count * 3000)))
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)
        send_times.append((self.frame_count * 3000 - 3000, time.time()))
        return video_frame
    
    async def process_frame(self, message):
        arrival_time = time.time()
        global arms_exercise_reps, arrival_times
        #self.fps+=1
        #if (time.time() - self.start_time > 1):
            #print(self.fps, "fps")
            #self.fps = 0
            #self.start_time = time.time()

        try:
            data = pickle.loads(message)
            frame_count = data.get("frame_count", 0)
            arrival_times.append((frame_count, arrival_time))
            if frame_count == 0:
                return
            landmarks = data.get("landmarks", None)
            while self.frames:
                frame, pts = self.frames.pop(0)
                if pts == frame_count:
                    if landmarks:
                        """
                        styled_connections = arms_exercise(landmarks)
                        if styled_connections:
                            mp_drawing.draw_landmarks(
                                image=frame,
                                landmark_list=landmarks,
                                connections=utils._POSE_CONNECTIONS,
                                connection_drawing_spec=styled_connections,
                            )
                        else:"""
                        utils.new_draw_landmarks(
                                image=frame,
                                landmark_list=landmarks,
                                connections=utils._POSE_CONNECTIONS,
                            )
                    cv2.putText(frame, f"Repetitions: {arms_exercise_reps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                    cv2.imshow("MediaPipe Pose", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    break
        except Exception as e:
            print("Error processing message:", e)
    
async def run(ip_address, port):
    signaling = TcpSocketSignaling(ip_address, port)
    pc = RTCPeerConnection()
    video_track = VideoTrack(0)
    pc.addTrack(video_track)
    print("Added video track")

    try:
        await signaling.connect()
        print("Connecting to server")

        data_channel = pc.createDataChannel("data")

        @data_channel.on("open")
        def on_open():
            print("Data channel is open")

        @data_channel.on("message")
        def on_message(message):
            asyncio.create_task(video_track.process_frame(message))

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is", pc.connectionState)
            if pc.connectionState == "connected":
                print("WebRTC connected")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await signaling.send(pc.localDescription)

        while True:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                print("Received offer")
                break
            elif obj is None:
                print("Received None")
                break

        # Run until the connection is closed or user interrupts
        while True:
            await asyncio.sleep(1)
            if pc.connectionState == "closed":
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        print("Closing connection")
        
        await signaling.close()
        await pc.close()
        
    except Exception as e:
        print(e)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    ip_address = "0.0.0.0"
    port = 9999
    time_offset = utils.ntp_sync()
    try:
        asyncio.run(run(ip_address, port))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        exit(0)
        # create folder with actual date and time
        import os
        from datetime import datetime
        now = datetime.now()
        folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs(folder_name, exist_ok=True)
        os.chdir(folder_name)
        # save send_times and arrival_times to csv files
        with open("point_a.csv", "w") as f:
            f.write("frame_count,raw_send_time,send_time\n")
            for send_time in send_times:
                f.write(f"{send_time[0]},{send_time[1]},{time_offset + send_time[1]}\n")

        with open("point_f.csv", "w") as f:
            f.write("frame_count,raw_arrival_time,arrival_time\n")
            for arrival_time in arrival_times:
                f.write(f"{arrival_time[0]},{arrival_time[1]},{time_offset + arrival_time[1]}\n")
        print("Data saved to CSV files")
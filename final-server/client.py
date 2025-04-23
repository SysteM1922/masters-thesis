import asyncio
import fractions
import pickle
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp
import cv2
import time
import utils

mp_drawing = mp.solutions.drawing_utils

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
        self.times = []
        #self.fps = 0
        #self.start_time = time.time()

    async def recv(self):
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
        self.times.append(time.perf_counter())
        return video_frame
    
    async def process_frame(self, message):
        #self.fps+=1
        #if (time.time() - self.start_time > 1):
            #print(self.fps, "fps")
            #self.fps = 0
            #self.start_time = time.time()

        try:
            data = pickle.loads(message)
            frame_count = data.get("frame_count", 0)
            print(time.perf_counter() - self.times[frame_count // 3000], "s")
            if frame_count == 0:
                return
            landmarks = data.get("landmarks", None)
            while self.frames:
                frame, pts = self.frames.pop(0)
                if pts == frame_count:
                    if landmarks:
                        mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=landmarks,
                            connections=mp.solutions.pose.POSE_CONNECTIONS,
                        )
                        mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=landmarks,
                            connections=utils._ARMS_AND_HANDS_CONNECTIONS,
                            connection_drawing_spec=utils._GREEN_STYLE,
                        )
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
        print("Connected to server")

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
            elif obj is None:
                print("Received None")
                break
        print("Closing connection")
        
    except Exception as e:
        print(e)
        await signaling.close()
        await pc.close()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    ip_address = "0.0.0.0"
    port = 9999
    try:
        asyncio.run(run(ip_address, port))
    except KeyboardInterrupt:
        pass
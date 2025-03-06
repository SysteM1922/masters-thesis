import asyncio
import fractions
import pickle
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp
import cv2

mp_drawing = mp.solutions.drawing_utils

class VideoTrack(VideoStreamTrack):
    def __init__(self, path):
        super().__init__()
        width = 1280
        height = 720
        self.cap = cv2.VideoCapture(path)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.frame_count = 0
        self.frames = []

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
        return video_frame
    
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
            try:
                data = pickle.loads(message)
                frame_count = data.get("frame_count", 0)
                if frame_count == 0:
                    return
                landmarks = data.get("landmarks", None)
                
                while video_track.frames:
                    frame, pts = video_track.frames.pop(0)
                    if pts == frame_count:
                        if landmarks:
                            mp_drawing.draw_landmarks(frame, landmarks, mp.solutions.pose.POSE_CONNECTIONS)
                        cv2.imshow("MediaPipe Pose", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                        break

            except Exception as e:
                print("Error processing message:", e)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is", pc.connectionState)
            if pc.connectionState == "connected":
                print("WebRTC connected")

        # send offer
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
    ip_address = "localhost"
    port = 9999
    try:
        asyncio.run(run(ip_address, port))
    except KeyboardInterrupt:
        pass
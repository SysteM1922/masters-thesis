import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

processing = False

async def mediapipe_pose(frame):
    global processing
    frame = frame.to_ndarray(format="bgr24")
    image = cv2.flip(frame, 1)
    results = pose.process(image)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    cv2.imshow("frame", image)
    processing = False

class VideoReceiver:
    async def handle_track(self, track):
        global processing
        while True:
            try:
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                if processing:
                    continue

                if isinstance(frame, VideoFrame):
                    processing = True
                elif isinstance(frame, np.ndarray):
                    print(f"Frame type: numpy array")
                else:
                    print(f"Frame type: {type(frame)}")
                    continue
                
                asyncio.ensure_future(mediapipe_pose(frame))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except asyncio.TimeoutError:
                print("Timeout")
            except Exception as e:
                print(e)
                break
        
async def run(pc, signaling):
    await signaling.connect()
    print("Connected to server")

    @pc.on("track")
    def on_track(track):
        print("Track received")
        asyncio.ensure_future(video_receiver.handle_track(track))

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data channel opened")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is", pc.connectionState)
        if pc.connectionState == "connected":
            print("WebRTC connected")

    # receive offer
    offer = await signaling.receive()
    print("Received offer")
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await signaling.send(pc.localDescription)
    print("Sent answer")

    while pc.connectionState != "connected":
        await asyncio.sleep(0.1)

    await asyncio.sleep(30)

    print("Closing")

if __name__ == "__main__":
    global video_receiver
    video_receiver = VideoReceiver()

    pc = RTCPeerConnection()
    signaling = TcpSocketSignaling("192.168.1.100", 9999)
    receiver = VideoReceiver()
    asyncio.run(run(pc, signaling))
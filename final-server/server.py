import asyncio
import json
from aiortc import RTCPeerConnection, RTCDataChannel, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp
import pickle
import time
from pymongo import MongoClient

client = MongoClient("mongodb://10.255.40.73:27017/")
db = client["gym"]
colection = db["exercise_data"]

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

class VideoReceiver:
    def __init__(self):
        self.data_channel = None
        self.lock = asyncio.Lock()
        self.start_timer_to_send_to_db = 0
        self.data_to_send_to_db = []

    async def send_to_db(self, data, frame_nr):

        if data:
            data = {
                "pose_landmarks": [
                    {
                        "point_index": idx,
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z,
                        "visibility": landmark.visibility
                    } for idx, landmark in enumerate(data.landmark)
                ],
                "frame_nr": frame_nr,
            }
            self.data_to_send_to_db.append(data)

        if self.start_timer_to_send_to_db == 0:
            self.start_timer_to_send_to_db = time.time()
        if time.time() - self.start_timer_to_send_to_db > 5:
            if self.data_to_send_to_db:
                data = {
                    "timestamp": time.time(),
                    "landmarks": self.data_to_send_to_db,
                }
                colection.insert_one(data)
            self.data_to_send_to_db = []
            self.start_timer_to_send_to_db = time.time()

    async def process_frame(self, frame):
        async with self.lock:
            try: 
                image = frame.to_ndarray(format="bgr24")
                perf_time = time.perf_counter()
                results = pose.process(image)
                print(time.perf_counter() - perf_time, "s")

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks
                else:
                    landmarks = None

                asyncio.create_task(self.send_to_db(landmarks, frame.pts))

                data = pickle.dumps({
                    "landmarks": landmarks,
                    "frame_count": frame.pts
                })

                if self.data_channel and self.data_channel.readyState == "open":
                    self.data_channel.send(data)
                else:
                    print("Data channel is not open")
            except Exception as e:
                print("Error processing frame:", e)
            
    async def handle_track(self, track):
        timeouts = 0
        while True:
            try:
                if self.lock.locked():
                    print("Video receiver is locked")
                    continue
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                if isinstance(frame, VideoFrame):
                    await self.process_frame(frame)
                else:
                    print(f"Frame type: {type(frame)}")
                timeouts = 0
            except asyncio.TimeoutError:
                print("Timeout")
                timeouts += 1
                if timeouts > 4:
                    break
            except Exception as e:
                print("Error receiving frame:", e)
                break

async def run(ip_adress, port):
    while True:
        try:
            signaling = TcpSocketSignaling(ip_adress, port)
            await signaling.connect()

            pc = RTCPeerConnection()
            video_receiver = VideoReceiver()
            
            @pc.on("datachannel")
            def on_datachannel(channel):
                print("Data channel opened")
                video_receiver.data_channel = channel

                @channel.on("stop")
                def on_stop():
                    print("Data channel closed")
                    channel.close()

            @pc.on("track")
            def on_track(track):
                print("Track received")
                asyncio.ensure_future(video_receiver.handle_track(track))

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                print("Connection state is", pc.connectionState)
                if pc.connectionState == "connected":
                    print("WebRTC connected")

            # receive offer
            offer = await signaling.receive()
            await pc.setRemoteDescription(offer)

            # send answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
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
        except ConnectionRefusedError:
            await asyncio.sleep(2)  # Retry every 2 seconds
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    ip_adress = "localhost"
    port = 9999
    asyncio.run(run(ip_adress, port))

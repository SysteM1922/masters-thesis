import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame

class VideoReceiver:
    def __init__(self):
        self.track = None

    async def handle_track(self, track):
        self.track = track
        frame_count = 0
        while True:
            print("Waiting for frame")
            try:
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                frame_count += 1
                print(f"Received frame {frame_count}")

                if isinstance(frame, VideoFrame):
                    print(f"Frame type: VideoFrame, pts:, {frame.pts}, time_base: {frame.time_base}")
                    frame = frame.to_ndarray(format="bgr24")
                elif isinstance(frame, np.ndarray):
                    print(f"Frame type: numpy array")
                else:
                    print(f"Frame type: {type(frame)}")
                    continue
                
                cv2.imshow("frame", frame)
                print("Showing frame")
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
    signaling = TcpSocketSignaling("localhost", 9999)
    receiver = VideoReceiver()
    asyncio.run(run(pc, signaling))
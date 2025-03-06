import asyncio
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import fractions

class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, path):
        super().__init__()
        width = 3840
        height = 2160
        self.cap = cv2.VideoCapture(path)
        self.cap.set(3, width)
        self.cap.set(4, height)

        self.frame_count = 0

    async def recv(self):
        self.frame_count += 1
        print(f"Sending frame {self.frame_count}")
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera")
            return None

        frame = cv2.resize(frame, (640, 480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)  # Use fractions for time_base
        return video_frame

async def run(ip_address, port, path):
    signaling = TcpSocketSignaling(ip_address, port)
    pc = RTCPeerConnection()
    # add video track
    video_sender = CustomVideoStreamTrack(path)
    pc.addTrack(video_sender)
    print("Added video track")

    try:
        await signaling.connect()
        print("Connected to server")

        @pc.on("datachannel")
        def on_datachannel(channel):
            print("Data channel opened")

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
    finally:
        await pc.close()

async def main():
    ip_address = "localhost"
    port = 9999
    path = 0
    await run(ip_address, port, path)

if __name__ == "__main__":
    asyncio.run(main())
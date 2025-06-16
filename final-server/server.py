import json
from aiortc import RTCPeerConnection, RTCSessionDescription
import av
import mediapipe as mp
from mediapipe.tasks.python import vision
import time
import asyncio
import threading
from dataclasses import asdict
import sys
from api_interface import TestsAPI

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

IP_ADDRESS = "0.0.0.0"
PORT = 9999

test_id = None

last_frame = None
data_channel = None
pose_thread = True

arrival_times = []
start_process_times = []
end_process_times = []
send_times = []

base_options = mp.tasks.BaseOptions(
    model_asset_path="../models/pose_landmarker_full.task", # Path to the model file
    delegate=mp.tasks.BaseOptions.Delegate.CPU, # Use GPU if available (only on Linux)
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

detector = vision.PoseLandmarker.create_from_options(options)
    
async def handle_results(results, frame_pts):
    global data_channel, send_times
    if results.pose_landmarks:
        landmarkslist = [asdict(landmark) for landmark in results.pose_landmarks[0]]
    else:
        landmarkslist = []

    data = json.dumps({
        "landmarks": landmarkslist,
        "frame_count": frame_pts
    })

    try:
        # Check if data_channel exists and is open before sending
        if data_channel and data_channel.readyState == "open":
            send_times.append((frame_pts, time.time()))
            data_channel.send(data)
    except Exception as e:
        print(f"Error sending data: {e}")

def process_frame():
    global last_frame, pose_thread, start_process_times, end_process_times
    while pose_thread:
        frame = last_frame
        if not frame:
            # If no frame is available, wait for a short time before checking again
            time.sleep(0.01)
            continue
        start_process_times.append((frame.pts, time.time()))
        last_frame = None
        try:
            image = frame.to_ndarray(format="bgr24")
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            results = detector.detect(mp_image)
            end_process_times.append((frame.pts, time.time()))
            print(end_process_times[-1][1] - start_process_times[-1][1]) 
            result = asyncio.run(handle_results(results, frame.pts))
        except Exception as e:
            print("Error processing frame:", e)
            continue
        

class VideoReceiver:
    def __init__(self):
        self.start_timer_to_send_to_db = 0
        self.data_to_send_to_db = []

    async def handle_track(self, track):
        global last_frame, pose_thread, arrival_times
        process_thread = threading.Thread(target=process_frame)
        process_thread.daemon = True  # Make thread daemon so it terminates when main thread exits
        process_thread.start()
        
        timeouts = 0
        while True:
            try:
                if not pose_thread:
                    break
                    
                frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                arrival_time = time.time()
                if isinstance(frame, av.VideoFrame):
                    arrival_times.append((frame.pts, arrival_time))
                    last_frame = frame
                else:
                    print(f"Frame type: {type(frame)}")
                timeouts = 0
            except asyncio.TimeoutError:
                print("Timeout")
                timeouts += 1
                if timeouts > 4:
                    break
            except Exception as e:
                print(f"Error receiving frame: {e}")
                break

        pose_thread = False
        print("Track handler terminated")

class TcpSocketSignalingServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        print(f"Signaling server started on {self.host}:{self.port}")
        return server
    
    async def handle_client(self, reader, writer):
        self.reader = reader
        self.writer = writer
        print("Client connected")

    async def send(self, obj):
        if self.writer is None:
            raise ConnectionError("Not connected to a client")
        
        if hasattr(obj, 'sdp'):
            message = { "sdp": obj.sdp, "type": obj.type}
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
            return message
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
        
    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
async def run(ip_adress, port):
    global pose_thread, data_channel

    signaling = TcpSocketSignalingServer(ip_adress, port)
    server = await signaling.start_server()

    try:
        while True:

            print("Waiting for client to connect...")
            while signaling.writer is None:
                await asyncio.sleep(0.1)

            try:
                pc_config = {

                }
                pc = RTCPeerConnection(pc_config)
                video_receiver = VideoReceiver()

                # Reset global state for new connection
                pose_thread = True
                data_channel = None

                @pc.on("datachannel")
                def on_datachannel(channel):
                    print("Data channel opened")
                    global data_channel
                    data_channel = channel

                    @channel.on("close")
                    def on_close():
                        print("Data channel closed")
                        global data_channel
                        data_channel = None

                    @channel.on("stop")
                    def on_stop():
                        print("Data channel stopped")
                        global data_channel
                        data_channel = None
                        channel.close()

                    @channel.on("message")
                    def on_message(message):
                        global test_id
                        print("Message received:", message)
                        if isinstance(message, str):
                            try:
                                data = json.loads(message)
                                if "test_id" in data:
                                    test_id = data["test_id"]
                            except json.JSONDecodeError:
                                print("Received non-JSON message:", message)

                @pc.on("track")
                def on_track(track):
                    print("Track received")
                    asyncio.create_task(video_receiver.handle_track(track))

                @pc.on("connectionstatechange")
                async def on_connectionstatechange():
                    print("Connection state is", pc.connectionState)
                    if pc.connectionState == "connected":
                        print("WebRTC connected")
                    elif pc.connectionState in ["closed", "failed", "disconnected"]:
                        print("WebRTC connection ended:", pc.connectionState)
                        global pose_thread
                        pose_thread = False
                        await pc.close()
                        await signaling.close()

                print("Waiting for offer...")
                # receive offer
                offer = await signaling.receive()
                if not offer:
                    print("No offer received")
                    continue

                await pc.setRemoteDescription(offer)

                print("Received offer, creating answer...")
                # send answer
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await signaling.send(pc.localDescription)

                # Process signaling messages
                print("WebRTC connection established")
                while True:
                    try:
                        obj = await signaling.receive()
                        if isinstance(obj, RTCSessionDescription):
                            await pc.setRemoteDescription(obj)
                            print("Received remote description")
                        elif obj is None:
                            print("Signaling connection closed")
                            break
                    except Exception as e:
                        print(f"Signaling error: {e}")
                        break

                pose_thread = False
                
                await pc.close()
                signaling.writer.close()
                await signaling.writer.wait_closed()

                signaling.writer = None
                signaling.reader = None
                break

            except Exception as e:
                print(f"Server error: {e}")
                break

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        print("Closing server...")
        server.close()
        print("Server closed")
        #await server.wait_closed() # broken according to the documentation

if __name__ == "__main__":
    try:
        asyncio.run(run(IP_ADDRESS, PORT))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        detector.close()
        #exit(0)

        print("Adding measurements to the test. Please wait...")

        for arrival_time in arrival_times:
            TestsAPI.add_measurement(
                test_id=test_id,
                timestamp=arrival_time[1],
                point="{\"point_b\": " + str(arrival_time[0]) + "}"
            )

        for start_process_time in start_process_times:
            TestsAPI.add_measurement(
                test_id=test_id,
                timestamp=start_process_time[1],
                point="{\"point_c\": " + str(start_process_time[0]) + "}"
            )

        for end_process_time in end_process_times:
            TestsAPI.add_measurement(
                test_id=test_id,
                timestamp=end_process_time[1],
                point="{\"point_d\": " + str(end_process_time[0]) + "}"
            )

        for send_time in send_times:
            TestsAPI.add_measurement(
                test_id=test_id,
                timestamp=send_time[1],
                point="{\"point_e\": " + str(send_time[0]) + "}"
            )
            
        print("Test completed and measurements added.")
        print(f"Test ID: {test_id}")
        exit(0)

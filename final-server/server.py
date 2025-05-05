import json
from aiortc import RTCPeerConnection, RTCDataChannel, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp
import pickle
import time
import asyncio
import threading
from pymongo import MongoClient
import utils

client = MongoClient("mongodb://10.255.40.73:27017/")
db = client["gym"]
colection = db["exercise_data"]
last_frame = None
data_channel = None
pose_thread = True

arrival_times = []
start_process_times = []
end_process_times = []
send_times = []

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    model_complexity=1,
    min_detection_confidence=0.9,
    min_tracking_confidence=0.5)

async def handle_results(results, frame_pts):
    global data_channel, send_times
    if results.pose_landmarks:
        landmarks = results.pose_landmarks
    else:
        landmarks = None

    data = pickle.dumps({
        "landmarks": landmarks,
        "frame_count": frame_pts
    })

    try:
        # Check if data_channel exists and is open before sending
        if data_channel and data_channel.readyState == "open":
            send_times.append((frame_pts, utils.get_ntp_time()))
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
        start_process_times.append((frame.pts, utils.get_ntp_time()))
        last_frame = None
        try:
            image = frame.to_ndarray(format="bgr24")
            #perf_time = time.perf_counter()
            results = pose.process(image)
            end_process_times.append((frame.pts, utils.get_ntp_time()))
            #print(time.perf_counter() - perf_time, "s")
            result = asyncio.run(handle_results(results, frame.pts))
        except Exception as e:
            print("Error processing frame:", e)
            continue
        

class VideoReceiver:
    def __init__(self):
        self.start_timer_to_send_to_db = 0
        self.data_to_send_to_db = []

    async def send_to_db(self, data, frame_nr):

        if data:
            data = {
                "pose_landmarks": data.landmark,
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
            
    async def handle_track(self, track):
        global last_frame, pose_thread, arrival_times
        process_thread = threading.Thread(target=process_frame)
        process_thread.daemon = True  # Make thread daemon so it terminates when main thread exits
        process_thread.start()
        
        timeouts = 0
        try:
            while True:
                try:
                    if not pose_thread:
                        break
                        
                    frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                    if isinstance(frame, VideoFrame):
                        arrival_times.append((frame.pts, utils.get_ntp_time()))
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
        finally:
            pose_thread = False
            print("Track handler terminated")

async def run(ip_adress, port):
    global pose_thread, data_channel
    while True:
        try:
            signaling = TcpSocketSignaling(ip_adress, port)
            await signaling.connect()

            pc = RTCPeerConnection()
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

            # receive offer
            offer = await signaling.receive()
            if not offer:
                print("No offer received")
                continue
                
            await pc.setRemoteDescription(offer)

            # send answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await signaling.send(pc.localDescription)

            # Process signaling messages
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
                    
            print("Closing connection")
            pose_thread = False
            await pc.close()
            await signaling.close()
            
        except ConnectionRefusedError:
            print("Connection refused, retrying in 2 seconds")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(2)  # Add delay before retry on general errors

if __name__ == "__main__":
    ip_adress = "localhost"
    port = 9999
    #time_offset = utils.ntp_sync()
    try:
        asyncio.run(run(ip_adress, port))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pose.close()

        with open("server_arrival_times.csv", "w") as f:
            for arrival_time in arrival_times:
                f.write(f"{arrival_time[0]},{arrival_time[1]}\n")

        with open("server_start_process_times.csv", "w") as f:
            for start_process_time in start_process_times:
                f.write(f"{start_process_time[0]},{start_process_time[1]}\n")

        with open("server_end_process_times.csv", "w") as f:
            for end_process_time in end_process_times:
                f.write(f"{end_process_time[0]},{end_process_time[1]}\n")

        with open("server_send_times.csv", "w") as f:
            for send_time in send_times:
                f.write(f"{send_time[0]},{send_time[1]}\n")

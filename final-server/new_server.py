import json
from aiortc import RTCPeerConnection, RTCDataChannel, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import mediapipe as mp
from mediapipe.tasks.python import vision
import pickle
import time
import asyncio
import threading
from pymongo import MongoClient
import utils
import psutil

client = MongoClient("mongodb://10.255.40.73:27017/")
db = client["gym"]
colection = db["exercise_data"]
data_channel = None
process_flag = True
frame_id = -1

arrival_times = []
start_process_times = []
end_process_times = []
send_times = []

base_options = mp.tasks.BaseOptions(
    model_asset_path="../models/pose_landmarker_full.task", # Path to the model file
    delegate=mp.tasks.BaseOptions.Delegate.GPU, # Use GPU if available (only on Linux)
)

def handle_results(results, output_image=None, timestamp=None):
    """Non-async version that calls the real handler in the main event loop"""
    end_process_time = time.time()
    global data_channel, send_times, start_process_times, end_process_times, process_flag, frame_id
    
    # Add results to process times tracking
    start_process_times.append((frame_id, timestamp))
    end_process_times.append((frame_id, end_process_time))
    
    # Extract landmarks
    landmarks = None
    if results.pose_landmarks:
        landmarks = results.pose_landmarks[0]
    
    # Package data
    data = pickle.dumps({
        "landmarks": landmarks,
        "frame_count": frame_id,
    })
    
    # Get the main event loop and schedule sending data
    loop = asyncio.get_event_loop_policy().get_event_loop()
    
    def send_data_in_main_loop():
        global process_flag
        try:
            if data_channel and data_channel.readyState == "open":
                send_times.append((timestamp, time.time()))
                asyncio.create_task(data_channel.send(data))
            process_flag = True
        except Exception as e:
            print(f"Error in send_data_in_main_loop: {e}")
            process_flag = True
    
    # Schedule the send operation in the main event loop
    loop.call_soon_threadsafe(send_data_in_main_loop)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    result_callback=handle_results,
    num_poses=1,
    min_tracking_confidence=0.5,
)

detector = vision.PoseLandmarker.create_from_options(options)
        

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
        global arrival_times, process_flag, frame_id
        
        timeouts = 0
        try:
            while True:
                try:
                    frame = await asyncio.wait_for(track.recv(), timeout=5.0)
                    arrival_time = time.time()
                    if process_flag:
                        if isinstance(frame, VideoFrame):
                            try:
                                process_flag = False
                                frame_id = frame.pts
                                arrival_times.append((frame_id, arrival_time))
                                image = frame.to_ndarray(format="bgr24")
                                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
                                start_process_times.append((frame_id, time.time()))
                                detector.detect_async(mp_image, timestamp_ms=int(time.time() * 1000))
                            except Exception as e:
                                print("Error processing frame:", e)
                                continue
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
            print("Track handler terminated")

async def run(ip_adress, port):
    global data_channel
    while True:
        try:
            signaling = TcpSocketSignaling(ip_adress, port)
            await signaling.connect()

            pc = RTCPeerConnection()
            video_receiver = VideoReceiver()
            
            # Reset global state for new connection
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
                    
            print("Closing connection")
            await pc.close()
            await signaling.close()
            
        except ConnectionRefusedError:
            print("Connection refused, retrying in 2 seconds")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(2)  # Add delay before retry on general errors

if __name__ == "__main__":
    ip_adress = "192.168.1.157" # Replace with your server's IP address
    port = 9999
    time_offset = utils.ntp_sync()
    try:
        asyncio.run(run(ip_adress, port))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        detector.close()
        exit(0)

        with open("point_b.csv", "w") as f:
            f.write("frame_count,raw_arrival_time,arrival_time\n")
            for arrival_time in arrival_times:
                f.write(f"{arrival_time[0]},{arrival_time[1]},{time_offset + arrival_time[1]}\n")

        with open("point_c.csv", "w") as f:
            f.write("frame_count,raw_start_process_time,start_process_time\n")
            for start_process_time in start_process_times:
                f.write(f"{start_process_time[0]},{start_process_time[1]},{time_offset + start_process_time[1]}\n")

        with open("point_d.csv", "w") as f:
            f.write("frame_count,raw_end_process_time,end_process_time\n")
            for end_process_time in end_process_times:
                f.write(f"{end_process_time[0]},{end_process_time[1]},{time_offset + end_process_time[1]}\n")

        with open("point_e.csv", "w") as f:
            f.write("frame_count,raw_send_time,send_time\n")
            for send_time in send_times:
                f.write(f"{send_time[0]},{send_time[1]},{time_offset + send_time[1]}\n")
        print("Data saved to CSV files")

import time
import mediapipe as mp
from mediapipe.tasks.python import vision
import cv2
from mediapipe.framework.formats import landmark_pb2 as mp_landmark
import utils

mp_pose = mp.solutions.pose

mp_drawing = mp.solutions.drawing_utils

time_stamp = 0
results = None

def update_results(result, output_image=None, timestamp=None):
    print(time.perf_counter() - time_stamp)
    global results
    results = result

base_options = mp.tasks.BaseOptions(
    model_asset_path="pose_landmarker_lite.task",
    delegate=mp.tasks.BaseOptions.Delegate.CPU,
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_poses=1,
    min_tracking_confidence=0.5,
    result_callback=update_results,
)

detector = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from camera")
        break

    image = cv2.flip(frame, 1)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    time_stamp = time.perf_counter()
    detector.detect_async(mp_image, timestamp_ms=int(time.time() * 1000))

    if results is not None and results.pose_landmarks:
        utils.new_draw_landmarks(image, results.pose_landmarks[0], mp_pose.POSE_CONNECTIONS)

    cv2.imshow("frame", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()
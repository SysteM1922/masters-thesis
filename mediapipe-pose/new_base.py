import time
import mediapipe as mp
from mediapipe.tasks.python import vision
import cv2
from mediapipe.framework.formats import landmark_pb2 as mp_landmark

mp_pose = mp.solutions.pose

results = None

def update_results(result, output_image=None, timestamp=None):
    global results
    results = result

base_options = mp.tasks.BaseOptions(
    model_asset_path="pose_landmarker_lite.task",
    delegate=mp.tasks.BaseOptions.Delegate.GPU,
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_poses=1,
    min_tracking_confidence=0.5,
    result_callback=update_results,
)

detector = vision.PoseLandmarker.create_from_options(options)

mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from camera")
        break

    image = cv2.flip(frame, 1)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
    detector.detect_async(mp_image, timestamp_ms=int(time.time() * 1000))
    """
    if results and results.pose_landmarks:
        landmarks = mp_landmark.NormalizedLandmarkList()
        for landmark in results.pose_landmarks:
            landmarks.landmark.extend([
                mp_landmark.NormalizedLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                )
            ])
        mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)
        """
    cv2.imshow("frame", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
import mediapipe as mp
import cv2
import time

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from camera")
        break

    image = cv2.flip(frame, 1)
    time_stamp = time.perf_counter()
    results = pose.process(image)
    print(time.perf_counter() - time_stamp)
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    cv2.imshow("frame", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
import mediapipe as mp
import cv2
import utils

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    model_complexity=1,
    min_detection_confidence=0.9,
    min_tracking_confidence=0.5)

class Joint:
    def __init__(self, joint):
        self.x = joint.x
        self.y = joint.y

right_arm_state_repetition = 0
right_arm_state = None

def right_arm_angle(right_shoulder, right_elbow, right_wrist):
    global right_arm_state_repetition, right_arm_state
    right_arm = None
    if right_shoulder.visibility > 0.5 and right_elbow.visibility > 0.5 and right_wrist.visibility > 0.5:
        new_right_shoulder = Joint(right_shoulder)
        new_right_shoulder.x = -right_shoulder.x
        new_right_wrist = Joint(right_wrist)
        new_right_wrist.x = -right_wrist.x
        right_arm_angle = utils.get_angle_2_points_x_axis(new_right_shoulder, new_right_wrist)
        right_elbow_angle = utils.get_angle_3_points(right_shoulder, right_elbow, right_wrist)

        if right_arm_angle < 10 and right_elbow_angle > 140:
            right_arm = True
        elif right_arm_angle > 60:
            right_arm = None
        else:
            right_arm = False

    if right_arm != right_arm_state:
        right_arm_state_repetition -= 1

        if right_arm == False and right_arm_state_repetition < -20:
            right_arm_state_repetition = 0
            right_arm_state = right_arm
        elif right_arm_state_repetition < 0:
            right_arm_state_repetition = 0
            right_arm_state = right_arm

    else: 
        if right_arm_state_repetition < 10:
            right_arm_state_repetition += 1

    return right_arm_state

left_arm_state_repetition = 0
left_arm_state = None

def left_arm_angle(left_shoulder, left_elbow, left_wrist):
    global left_arm_state_repetition, left_arm_state
    left_arm = None

    if left_shoulder.visibility > 0.5 and left_elbow.visibility > 0.5 and left_wrist.visibility > 0.5:
        left_arm_angle = utils.get_angle_2_points_x_axis(left_shoulder, left_wrist)
        left_elbow_angle = utils.get_angle_3_points(left_shoulder, left_elbow, left_wrist)
        
        if left_arm_angle < 10 and left_elbow_angle > 140:
            left_arm = True
        elif left_arm_angle > 60:
            left_arm = None
        else:
            left_arm = False

    if left_arm != left_arm_state:
        left_arm_state_repetition -= 1

        if left_arm == False and left_arm_state_repetition < -20:
            left_arm_state_repetition = 0
            left_arm_state = left_arm
        elif left_arm_state_repetition < 0:
            left_arm_state_repetition = 0
            left_arm_state = left_arm

    else:   
        if left_arm_state_repetition < 10:
            left_arm_state_repetition += 1

    return left_arm_state
    

def arms_angle(right_shoulder, left_shoulder, right_elbow, left_elbow, right_wrist, left_wrist):
    right_arm_state = right_arm_angle(right_shoulder, right_elbow, right_wrist) 
    left_arm_state = left_arm_angle(left_shoulder, left_elbow, left_wrist)

    return right_arm_state, left_arm_state

spine_state_repetition = 0
spine_state = None

def spine_straight(right_shoulder, left_shoulder, right_hip, left_hip):
    global spine_state_repetition, spine_state
    spine = None
    if right_shoulder.visibility > 0.5 and left_shoulder.visibility > 0.5 and right_hip.visibility > 0.5 and left_hip.visibility > 0.5:
        angle_shoulder_hip = utils.get_angle_4_points(right_shoulder, left_shoulder, right_hip, left_hip)
        new_left_shoulder = Joint(left_shoulder)
        new_left_shoulder.x = -left_shoulder.x
        new_right_shoulder = Joint(right_shoulder)
        new_right_shoulder.x = -right_shoulder.x
        new_right_hip = Joint(right_hip)
        new_right_hip.x = -right_hip.x
        angle_left_shoulder_hip = utils.get_angle_3_points(new_left_shoulder, new_right_shoulder, new_right_hip)
        angle_right_shoulder_hip = utils.get_angle_3_points(right_shoulder, left_shoulder, left_hip)
        
        if angle_shoulder_hip < 7 and angle_left_shoulder_hip - angle_right_shoulder_hip < 10:
            spine = True
        else:
            spine = False
    
    if spine != spine_state:
        spine_state_repetition -= 1

        if spine_state_repetition < 0:
            spine_state_repetition = 0
            spine_state = spine

    else:
        if spine_state_repetition < 10:
            spine_state_repetition += 1

    return spine_state

arms_exercise_state_repetition = 0
arms_exercise_state = None
old_arms_exercise_state = None
arms_exercise_reps = 0

def arms_exercise(landmarks):
    global arms_exercise_state_repetition, arms_exercise_state, arms_exercise_reps, old_arms_exercise_state

    spine_state = spine_straight(
        landmarks.landmark[12],
        landmarks.landmark[11],
        landmarks.landmark[24],
        landmarks.landmark[23]
    )

    right_arm_state, left_arm_state = arms_angle(
        landmarks.landmark[12],
        landmarks.landmark[11],
        landmarks.landmark[14],
        landmarks.landmark[13],
        landmarks.landmark[16],
        landmarks.landmark[15]
    )

    arms_exercise = None

    if right_arm_state is None and left_arm_state is None:
        arms_exercise = None

    elif right_arm_state and left_arm_state and spine_state:
        arms_exercise = True

    elif not right_arm_state or not left_arm_state or not spine_state:
        arms_exercise = False

    if arms_exercise != arms_exercise_state:
        arms_exercise_state_repetition -= 1

        if arms_exercise_state_repetition < 0:
            arms_exercise_state_repetition = 0
            if arms_exercise == True and (old_arms_exercise_state is None or arms_exercise_state is None):
                arms_exercise_reps += 1
                
            old_arms_exercise_state = arms_exercise_state
            arms_exercise_state = arms_exercise
    else:
        if arms_exercise_state_repetition < 5:
            arms_exercise_state_repetition += 1

    right_arm_style = utils.GREEN_STYLE if left_arm_state else utils.RED_STYLE
    left_arm_style = utils.GREEN_STYLE if right_arm_state else utils.RED_STYLE
    torso_style = utils.GREEN_STYLE if spine_state else utils.RED_STYLE
    
    styled_connections = utils.get_colored_style(
        right_arm= None if arms_exercise is None else right_arm_style,
        left_arm= None if arms_exercise is None is None else left_arm_style,
        torso= None if arms_exercise is None else torso_style,
    )
    return styled_connections

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from camera")
        break

    image = cv2.flip(frame, 1)
    results = pose.process(image)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks
        styled_connections = None #arms_exercise(landmarks)

        if styled_connections:
            mp_drawing.draw_landmarks(
                image=image,
                landmark_list=landmarks,
                connections=utils._POSE_CONNECTIONS,
                connection_drawing_spec=styled_connections,
            )
        else:
            mp_drawing.draw_landmarks(
                image=image,
                landmark_list=landmarks,
                connections=utils._POSE_CONNECTIONS,
            )

    cv2.putText(image, f"Repetitions: {arms_exercise_reps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.imshow("MediaPipe Pose", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
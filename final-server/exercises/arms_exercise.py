import utils
from copy import deepcopy

right_arm_state_repetition = 0
right_arm_state = None

def right_arm_angle(right_shoulder: dict, right_elbow: dict, right_wrist: dict):
    global right_arm_state_repetition, right_arm_state
    right_arm = None
    if right_shoulder['visibility'] > 0.5 and right_elbow['visibility'] > 0.5 and right_wrist['visibility'] > 0.5:
        new_right_shoulder = deepcopy(right_shoulder)
        new_right_shoulder['x'] = -right_shoulder['x']
        new_right_wrist = deepcopy(right_wrist)
        new_right_wrist['x'] = -right_wrist['x']
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

    if left_shoulder['visibility'] > 0.5 and left_elbow['visibility'] > 0.5 and left_wrist['visibility'] > 0.5:
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

def spine_straight(right_shoulder: dict, left_shoulder: dict, right_hip: dict, left_hip: dict):
    global spine_state_repetition, spine_state
    spine = None
    if right_shoulder['visibility'] > 0.5 and left_shoulder['visibility'] > 0.5 and right_hip['visibility'] > 0.5 and left_hip['visibility'] > 0.5:
        angle_shoulder_hip = utils.get_angle_4_points(right_shoulder, left_shoulder, right_hip, left_hip)
        angle_left_shoulder_hip = abs(utils.get_angle_3_points(left_shoulder, right_shoulder, right_hip) % 90)
        angle_right_shoulder_hip = abs(utils.get_angle_3_points(right_shoulder, left_shoulder, left_hip) % 90)
        if angle_shoulder_hip < 7 and angle_left_shoulder_hip - angle_right_shoulder_hip < 15:
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

def arms_exercise(landmarks, others):
    global arms_exercise_state_repetition, arms_exercise_state, old_arms_exercise_state

    new_rep = False

    # Check if we have enough landmarks (MediaPipe pose has 33 landmarks, indices 0-32)
    if not landmarks or len(landmarks) < 25:  # We need at least index 24
        styled_connections = {
            "right_arm": None,
            "left_arm": None,
            "torso": None
        }
        return styled_connections, new_rep

    spine_state = spine_straight(
        landmarks[12],
        landmarks[11],
        landmarks[24],
        landmarks[23]
    )

    right_arm_state, left_arm_state = arms_angle(
        landmarks[12],
        landmarks[11],
        landmarks[14],
        landmarks[13],
        landmarks[16],
        landmarks[15]
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
                new_rep = True

            old_arms_exercise_state = arms_exercise_state
            arms_exercise_state = arms_exercise
    else:
        if arms_exercise_state_repetition < 5:
            arms_exercise_state_repetition += 1

    right_arm_style = True if right_arm_state else False
    left_arm_style = True if left_arm_state else False
    torso_style = True if spine_state else False

    styled_connections = {
        "right_arm": None if arms_exercise is None else right_arm_style,
        "left_arm": None if arms_exercise is None else left_arm_style,
        "torso": None if arms_exercise is None else torso_style
    }

    return styled_connections, new_rep
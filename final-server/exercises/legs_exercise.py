import utils
import time

angle = 0
leg_exercise_started = None
start_clock = 0
sit_clock = 0
hip_y = 1

def legs_exercise(landmarks, right_leg: bool):
    global angle, leg_exercise_started, start_clock, sit_clock, hip_y

    try:
        new_rep = False

        if not landmarks or len(landmarks) < 33:  # We need at least index 32
            styled_connections = {
                "left_leg": None,
                "right_leg": None,
            }
            leg_exercise_started = None
            return styled_connections, new_rep

        if time.time() - start_clock < 1:
            return {
                "left_leg": True if not right_leg else None,
                "right_leg": True if right_leg else None,
            }, new_rep


        right_hip, right_knee, right_ankle, right_shoulder =  landmarks[24], landmarks[26], landmarks[28], landmarks[12]
        left_hip, left_knee, left_ankle, left_shoulder = landmarks[23], landmarks[25], landmarks[27], landmarks[11]

        if right_hip['visibility'] > 0.5 and left_hip['visibility'] > 0.5 and right_knee['visibility'] > 0.5 and left_knee['visibility'] > 0.5 and right_ankle['visibility'] > 0.5 and left_ankle['visibility'] > 0.5 and right_shoulder['visibility'] > 0.5 and left_shoulder['visibility'] > 0.5:
            right_knee_angle = int(utils.get_angle_3_points(
                right_hip, right_knee, right_ankle
            ))

            left_knee_angle = int(utils.get_angle_3_points(
                left_hip, left_knee, left_ankle
            ))

            right_hip_angle = int(utils.get_angle_3_points(
                right_shoulder, right_hip, right_knee
            ))

            left_hip_angle = int(utils.get_angle_3_points(
                left_shoulder, left_hip, left_knee
            ))

            right_thigh_length = utils.get_distance_2_points(right_hip, right_knee)

            left_thigh_length = utils.get_distance_2_points(left_hip, left_knee)

            right_leg_length = utils.get_distance_2_points(right_hip, right_ankle)

            left_leg_length = utils.get_distance_2_points(left_hip, left_ankle)

        else:
            leg_exercise_started = None
            return {
                "left_leg": None,
                "right_leg": None,
            }, new_rep

        correct = None
        sit = False

        if (right_hip_angle > 165 and (right_leg_length/right_thigh_length) < 2) or (left_hip_angle > 165 and (left_leg_length/left_thigh_length) < 2):
            sit_clock = time.time()
        else:
            sit = True

        if sit and time.time() - sit_clock > 1:

            knee_angle = right_knee_angle if right_leg else left_knee_angle
            hip = right_hip if right_leg else left_hip
            thigh_length = right_thigh_length if right_leg else left_thigh_length
            ankle = right_ankle if right_leg else left_ankle
            other_ankle = left_ankle if right_leg else right_ankle

            if leg_exercise_started is not None and knee_angle > 170 and thigh_length < 0.12 and (ankle['y'] + 0.02) < other_ankle['y'] and (hip_y - 0.1) < hip['y']:

                if not leg_exercise_started:
                    correct = True
                    new_rep = True
                    start_clock = time.time()

                leg_exercise_started = True

            elif knee_angle < 160:
                leg_exercise_started = False
                hip_y = left_hip['y'] if right_leg else right_hip['y']

        styled_connections = {
            "left_leg": correct if not right_leg else None,
            "right_leg": correct if right_leg else None
        }

        return styled_connections, new_rep
    
    except Exception as e:
        print(f"Error in legs_exercise: {e}")
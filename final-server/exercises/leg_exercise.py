import utils
import time

angle = 0
leg_exercise_started = None
start_clock = 0

def leg_exercise(landmarks, right_leg: bool):
    global angle, leg_exercise_reps, leg_exercise_started, start_clock

    new_rep = False

    if time.time() - start_clock < 1:
        return {
            "left_leg": True if right_leg else None,
            "right_leg": True if not right_leg else None,
        }, new_rep


    hip, knee, ankle = (23, 25, 27) if right_leg else (24, 26, 28)
    if landmarks[hip]['visibility'] > 0.5 and landmarks[knee]['visibility'] > 0.5 and landmarks[ankle]['visibility'] > 0.5:
        angle = utils.get_angle_3_points(
            landmarks[hip], landmarks[knee], landmarks[ankle]
        )
        angle = int(angle)
    
    else:
        angle = 0
        leg_exercise_started = None
        return {
            "left_leg": None,
            "right_leg": None,
        }, new_rep

    leg_style = None

    if angle > 170 and leg_exercise_started is not None:

        if not leg_exercise_started:
            leg_style = True
            new_rep = True
            start_clock = time.time()

        leg_exercise_started = True
    elif angle < 140:
        leg_exercise_started = False
    else:
        leg_style = None

    styled_connections = {
        "left_leg": leg_style if right_leg else None,
        "right_leg": leg_style if not right_leg else None
    }

    return styled_connections, new_rep
import utils
import time

angle = 0
leg_exercise_reps = 0
leg_exercise_started = None
start_clock = 0

def leg_exercise(landmarks, right_leg: bool):
    global angle, leg_exercise_reps, leg_exercise_started, start_clock

    if time.time() - start_clock < 1:
        return utils.get_colored_style(
        left_leg=utils.GREEN_STYLE if right_leg else utils.WHITE_STYLE,
        right_leg=utils.GREEN_STYLE if not right_leg else utils.WHITE_STYLE
        )


    hip, knee, ankle = (23, 25, 27) if right_leg else (24, 26, 28)
    if landmarks[hip]['visibility'] > 0.5 and landmarks[knee]['visibility'] > 0.5 and landmarks[ankle]['visibility'] > 0.5:
        angle = utils.get_angle_3_points(
            landmarks[hip], landmarks[knee], landmarks[ankle]
        )
        angle = int(angle)
    
    else:
        angle = 0
        leg_exercise_started = None
        return utils.get_colored_style(
            right_leg=utils.WHITE_STYLE,
            left_leg=utils.WHITE_STYLE,
        )

    leg_style = utils.WHITE_STYLE

    if angle > 170 and leg_exercise_started is not None:

        if not leg_exercise_started:
            leg_style = utils.GREEN_STYLE
            leg_exercise_reps += 1
            start_clock = time.time()

        leg_exercise_started = True
    elif angle < 140:
        leg_exercise_started = False
    else:
        leg_style = utils.WHITE_STYLE

    styled_connections = utils.get_colored_style(
        left_leg=leg_style if right_leg else utils.WHITE_STYLE,
        right_leg=leg_style if not right_leg else utils.WHITE_STYLE
    )

    return styled_connections
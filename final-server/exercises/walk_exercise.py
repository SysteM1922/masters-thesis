import utils
import time

correct_steps = 0
right_arm_angle_amp = 0
left_arm_angle_amp = 0
right_arm_rep_state = False
left_arm_rep_state = False
start_clock = 0

def walk_exercise(landmarks):

    global correct_steps, right_arm_angle_amp, left_arm_angle_amp, right_arm_rep_state, left_arm_rep_state, start_clock

    if landmarks[23]['visibility'] < 0.5 or landmarks[24]['visibility'] < 0.5 or landmarks[25]['visibility'] < 0.5 or landmarks[26]['visibility'] < 0.5 or landmarks[27]['visibility'] < 0.5 or landmarks[28]['visibility'] < 0.5:
        right_arm_angle_amp = 0
        left_arm_angle_amp = 0
        return None

    right_arm_angle_amp = utils.get_angle_3_points(
        landmarks[11], landmarks[13], landmarks[15]
    )

    left_arm_angle_amp = utils.get_angle_3_points(
        landmarks[12], landmarks[14], landmarks[16]
    )

    right_shoulder = landmarks[11]
    left_shoulder = landmarks[12]

    right_wrist = landmarks[15]
    left_wrist = landmarks[16]

    right_knee_y = landmarks[25]['y']
    left_knee_y = landmarks[26]['y']

    right_ankle_y = landmarks[27]['y']
    left_ankle_y = landmarks[28]['y']

    right_hip_x = landmarks[23]['x']
    left_hip_x = landmarks[24]['x']

    if right_wrist["x"] < right_hip_x:
        if right_arm_angle_amp < 140:
        
            left_arm_rep_state = False

            if time.time() - start_clock < 1:
                if right_arm_rep_state:
                
                    return utils.get_colored_style(
                        left_arm=utils.GREEN_STYLE,
                        right_leg=utils.GREEN_STYLE,
                    )

            elif right_arm_rep_state:
                return None

            right_arm_style = utils.RED_STYLE
            left_leg_style = utils.RED_STYLE

            if utils.get_distance_2_points(right_wrist, left_shoulder) < utils.get_distance_2_points(right_wrist, right_shoulder):
                right_arm_style = utils.GREEN_STYLE

            if left_knee_y + 0.02 < right_knee_y and left_ankle_y + 0.02 < right_ankle_y:
                left_leg_style = utils.GREEN_STYLE

            if left_leg_style == utils.GREEN_STYLE and right_arm_style == utils.GREEN_STYLE:
                correct_steps += 1
                right_arm_rep_state = True
                start_clock = time.time()

            return utils.get_colored_style(
                left_arm=right_arm_style,
                right_leg=left_leg_style
            )
    elif left_knee_y + 0.02 > right_knee_y:
        right_arm_rep_state = False

    if left_wrist["x"] > left_hip_x:
        if left_arm_angle_amp < 140:

            right_arm_rep_state = False

            if time.time() - start_clock < 1:
                if left_arm_rep_state:

                    return utils.get_colored_style(
                        right_arm=utils.GREEN_STYLE,
                        left_leg=utils.GREEN_STYLE,
                    )

            elif left_arm_rep_state:
                return None

            left_arm_style = utils.RED_STYLE
            right_leg_style = utils.RED_STYLE

            if utils.get_distance_2_points(left_wrist, right_shoulder) < utils.get_distance_2_points(left_wrist, left_shoulder):
                left_arm_style = utils.GREEN_STYLE

            if right_knee_y + 0.02 < left_knee_y and right_ankle_y + 0.02 < left_ankle_y:
                right_leg_style = utils.GREEN_STYLE

            if left_arm_style == utils.GREEN_STYLE and right_leg_style == utils.GREEN_STYLE:
                correct_steps += 1
                left_arm_rep_state = True
                start_clock = time.time()

            return utils.get_colored_style(
                right_arm=left_arm_style,
                left_leg=right_leg_style
            )

    elif right_knee_y + 0.02 > left_knee_y:
        left_arm_rep_state = False

    return None

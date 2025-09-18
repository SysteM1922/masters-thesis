import utils
import time

right_arm_angle_amp = 0
left_arm_angle_amp = 0
right_arm_rep_state = False
left_arm_rep_state = False
start_clock = 0

def walk_exercise(landmarks, others):

    global right_arm_angle_amp, left_arm_angle_amp, right_arm_rep_state, left_arm_rep_state, start_clock

    new_rep = False

    styled_connections = {
        "left_leg": None,
        "right_leg": None,
    }
    
    if not landmarks or len(landmarks) < 33:  # We need at least index 32
        right_arm_rep_state = False
        left_arm_rep_state = False
        return styled_connections, new_rep  
    if landmarks[23]['visibility'] < 0.5 or landmarks[24]['visibility'] < 0.5 or landmarks[25]['visibility'] < 0.5 or landmarks[26]['visibility'] < 0.5 or landmarks[27]['visibility'] < 0.5 or landmarks[28]['visibility'] < 0.5:
        right_arm_angle_amp = 0
        left_arm_angle_amp = 0
        return styled_connections, new_rep  
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
                
                    return {
                        "left_arm": True,
                        "right_leg": True,
                    }, new_rep  
            elif right_arm_rep_state:
                return styled_connections, new_rep  
            right_arm_style = False
            left_leg_style = False  
            if utils.get_distance_2_points(right_wrist, left_shoulder) < utils.get_distance_2_points(right_wrist, right_shoulder):
                right_arm_style = True  
            if left_knee_y + 0.02 < right_knee_y and left_ankle_y + 0.02 < right_ankle_y:
                left_leg_style = True   
            if left_leg_style and right_arm_style:
                new_rep = True
                right_arm_rep_state = True
                start_clock = time.time()   
            return {
                "left_arm": right_arm_style,
                "right_leg": left_leg_style
            }, new_rep  
    elif left_knee_y + 0.02 > right_knee_y:
        right_arm_rep_state = False 
    if left_wrist["x"] > left_hip_x:
        if left_arm_angle_amp < 140:    
            right_arm_rep_state = False 
            if time.time() - start_clock < 1:
                if left_arm_rep_state:  
                    return {
                        "right_arm": True,
                        "left_leg": True,
                    }, new_rep  
            elif left_arm_rep_state:
                return styled_connections, new_rep  
            left_arm_style = False
            right_leg_style = False 
            if utils.get_distance_2_points(left_wrist, right_shoulder) < utils.get_distance_2_points(left_wrist, left_shoulder):
                left_arm_style = True   
            if right_knee_y + 0.02 < left_knee_y and right_ankle_y + 0.02 < left_ankle_y:
                right_leg_style = True  
            if left_arm_style and right_leg_style:
                new_rep = True
                left_arm_rep_state = True
                start_clock = time.time()   
            return {
                "right_arm": left_arm_style,
                "left_leg": right_leg_style
            }, new_rep  
    elif right_knee_y + 0.02 > left_knee_y:
        left_arm_rep_state = False  
    return styled_connections, new_rep


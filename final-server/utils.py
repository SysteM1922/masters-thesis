from mediapipe.python.solutions.pose import PoseLandmark
from mediapipe.python.solutions.drawing_utils import DrawingSpec
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
import math
import datetime
import ntplib

ntp_client = ntplib.NTPClient()

def ntp_sync():
    try:
        response = ntp_client.request('pool.ntp.org', version=3)
        ntp_time = response.offset
        print("NTP Time:", ntp_time)
        return ntp_time
    except Exception as e:
        print("NTP synchronization failed:", e)
        return None

def get_ntp_time():
    """Get the current time from an NTP server."""
    try:
        response = ntp_client.request('pool.ntp.org', version=3)
        return response.tx_time
    except Exception as e:
        print("NTP synchronization failed:", e)
        return None

_GREEN = (48, 255, 48)
_RED = (0, 0, 255)
_WHITE = (255, 255, 255)

_POSE_CONNECTIONS = frozenset([(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5),
                              (5, 6), (6, 8), (9, 10), (11, 12), (11, 13),
                              (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
                              (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
                              (18, 20), (11, 23), (12, 24), (23, 24), (23, 25),
                              (24, 26), (25, 27), (26, 28), (27, 29), (28, 30),
                              (29, 31), (30, 32), (27, 31), (28, 32)])

_THICKNESS_CONTOURS = 5

GREEN_STYLE = DrawingSpec(color=_GREEN, thickness=_THICKNESS_CONTOURS)
WHITE_STYLE = DrawingSpec(color=_WHITE, thickness=_THICKNESS_CONTOURS)
RED_STYLE = DrawingSpec(color=_RED, thickness=_THICKNESS_CONTOURS)

_DEFAULT_POSE_LANDMARK_DRAWSPEC = {
    connection: WHITE_STYLE for connection in _POSE_CONNECTIONS
}

_LEFT_ARM_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_ELBOW),
     (PoseLandmark.LEFT_ELBOW, PoseLandmark.LEFT_WRIST)]
)

_LEFT_HAND_CONECTIONS = frozenset(
    [(PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_THUMB),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_INDEX),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_PINKY),
     (PoseLandmark.LEFT_INDEX, PoseLandmark.LEFT_PINKY)]
)

_RIGHT_ARM_CONNECTIONS = frozenset(
    [(PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW),
     (PoseLandmark.RIGHT_ELBOW, PoseLandmark.RIGHT_WRIST)]
)

_RIGHT_HAND_CONNECTIONS = frozenset(
    [(PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_THUMB),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_INDEX),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_PINKY),
     (PoseLandmark.RIGHT_INDEX, PoseLandmark.RIGHT_PINKY)]
)

_LEFT_ARM_AND_HAND_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_PINKY, PoseLandmark.LEFT_INDEX),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_PINKY),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_INDEX),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_THUMB),
     (PoseLandmark.LEFT_ELBOW, PoseLandmark.LEFT_WRIST),
     (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_ELBOW)]    
)

_RIGHT_ARM_AND_HAND_CONNECTIONS = frozenset(
    [(PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW),
     (PoseLandmark.RIGHT_ELBOW, PoseLandmark.RIGHT_WRIST),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_THUMB),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_INDEX),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_PINKY),
     (PoseLandmark.RIGHT_PINKY, PoseLandmark.RIGHT_INDEX)]    
)

_TORSO_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER),
     (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_HIP),
     (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_HIP),
     (PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP)]
)

_LEFT_LEG_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_HIP, PoseLandmark.LEFT_KNEE),
     (PoseLandmark.LEFT_KNEE, PoseLandmark.LEFT_ANKLE),
     (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_HEEL),
     (PoseLandmark.LEFT_HEEL, PoseLandmark.LEFT_FOOT_INDEX)]
)

_RIGHT_LEG_CONNECTIONS = frozenset(
    [(PoseLandmark.RIGHT_HIP, PoseLandmark.RIGHT_KNEE),
     (PoseLandmark.RIGHT_KNEE, PoseLandmark.RIGHT_ANKLE),
     (PoseLandmark.RIGHT_ANKLE, PoseLandmark.RIGHT_HEEL),
     (PoseLandmark.RIGHT_HEEL, PoseLandmark.RIGHT_FOOT_INDEX)]
)

_LEFT_LEG_AND_FOOT_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_HIP, PoseLandmark.LEFT_KNEE),
     (PoseLandmark.LEFT_KNEE, PoseLandmark.LEFT_ANKLE),
     (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_HEEL),
     (PoseLandmark.LEFT_HEEL, PoseLandmark.LEFT_FOOT_INDEX),
     (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_FOOT_INDEX)]
)

_RIGHT_LEG_AND_FOOT_CONNECTIONS = frozenset(
    [(PoseLandmark.RIGHT_HIP, PoseLandmark.RIGHT_KNEE),
     (PoseLandmark.RIGHT_KNEE, PoseLandmark.RIGHT_ANKLE),
     (PoseLandmark.RIGHT_ANKLE, PoseLandmark.RIGHT_HEEL),
     (PoseLandmark.RIGHT_HEEL, PoseLandmark.RIGHT_FOOT_INDEX),
     (PoseLandmark.RIGHT_ANKLE, PoseLandmark.RIGHT_FOOT_INDEX)]
)

def get_green_arms_and_hands_style() -> dict:
    """Returns the default pose arms and hands drawing style.

    Returns:
        A mapping from each pose landmark to its default drawing spec.
    """
    arms_and_hands_style = _DEFAULT_POSE_LANDMARK_DRAWSPEC
    
    for connection in _LEFT_ARM_AND_HAND_CONNECTIONS:
        arms_and_hands_style[connection] = GREEN_STYLE

    return arms_and_hands_style

def get_colored_style(right_arm: DrawingSpec = None, left_arm: DrawingSpec = None, torso: DrawingSpec = None, left_leg: DrawingSpec = None, right_leg: DrawingSpec = None) -> dict:
    """Returns a mapping from each pose landmark to its default drawing spec.

    Args:
        right_arm: The drawing spec for the right arm.
        left_arm: The drawing spec for the left arm.
        torso: The drawing spec for the torso.
        left_leg: The drawing spec for the left leg.
        right_leg: The drawing spec for the right leg.

    Returns:
        A mapping from each pose landmark to its default drawing spec.
    """

    colored_style = _DEFAULT_POSE_LANDMARK_DRAWSPEC.copy()

    if right_arm:
        for connection in _LEFT_ARM_AND_HAND_CONNECTIONS:
            colored_style[connection] = right_arm

    if left_arm:
        for connection in _RIGHT_ARM_AND_HAND_CONNECTIONS:
            colored_style[connection] = left_arm

    if torso:
        for connection in _TORSO_CONNECTIONS:
            colored_style[connection] = torso

    if left_leg:
        for connection in _LEFT_LEG_AND_FOOT_CONNECTIONS:
            colored_style[connection] = left_leg

    if right_leg:
        for connection in _RIGHT_LEG_AND_FOOT_CONNECTIONS:
            colored_style[connection] = right_leg

    return colored_style


def get_angle_4_points(p1, p2, p3, p4):
    """Calculate the angle between two vectors defined by four points.

    Args:
        p1: The first point of the first vector.
        p2: The second point of the first vector.
        p3: The first point of the second vector.
        p4: The second point of the second vector.

    Returns:
        The angle in degrees between the two vectors.
    """
    v1 = (p2.x - p1.x, p2.y - p1.y)
    v2 = (p4.x - p3.x, p4.y - p3.y)

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    magnitude_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0

    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
    angle = math.acos(cos_theta)

    return math.degrees(angle) if not math.isnan(angle) else None

def get_angle_3_points(p1, p2, p3):
    """Calculate the angle between two vectors defined by three points.

    Args:
        p1: The first point of the first vector.
        p2: The point where the two vectors meet.
        p3: The first point of the second vector.

    Returns:
        The angle in degrees between the two vectors.
    """
    
    return get_angle_4_points(p1, p2, p3, p2)

def get_angle_2_points_x_axis(p1, p2):
    """Calculate the angle between a vector defined by two points and the x-axis.

    Args:
        p1: The first point of the vector.
        p2: The second point of the vector.

    Returns:
        The angle in degrees between the vector and the x-axis.
    """
    
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    angle = math.atan2(dy, dx)
    return math.degrees(angle) if not math.isnan(angle) else None
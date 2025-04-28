from mediapipe.python.solutions.pose import PoseLandmark
from mediapipe.python.solutions.drawing_utils import DrawingSpec
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles

_GREEN = (48, 255, 48)
_RED = (255, 0, 0)
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

    colored_style = _DEFAULT_POSE_LANDMARK_DRAWSPEC

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

    
from mediapipe.python.solutions.pose import PoseLandmark
from mediapipe.python.solutions.drawing_utils import DrawingSpec

_GREEN = (48, 255, 48)

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

_ARMS_AND_HANDS_CONNECTIONS = frozenset(
    [(PoseLandmark.LEFT_INDEX, PoseLandmark.LEFT_PINKY),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_PINKY),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_INDEX),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_THUMB),
     (PoseLandmark.LEFT_WRIST, PoseLandmark.LEFT_ELBOW),
     (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_ELBOW),
     (PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER),
     (PoseLandmark.RIGHT_SHOULDER, PoseLandmark.RIGHT_ELBOW),
     (PoseLandmark.RIGHT_ELBOW, PoseLandmark.RIGHT_WRIST),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_THUMB),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_INDEX),
     (PoseLandmark.RIGHT_WRIST, PoseLandmark.RIGHT_PINKY),
     (PoseLandmark.RIGHT_INDEX, PoseLandmark.RIGHT_PINKY)]    
)

_GREEN_STYLE = DrawingSpec(color=_GREEN, thickness=2, circle_radius=2)
from dataclasses import dataclass
from mediapipe.python.solutions.pose import PoseLandmark
from mediapipe.python.solutions.drawing_utils import DrawingSpec
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
import math
from typing import Optional
import ntplib
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

def ntp_sync():
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org', version=3)
        ntp_time = response.offset
        print("NTP Time:", ntp_time)
        return ntp_time
    except Exception as e:
        print("NTP synchronization failed:", e)
        return None
    
def get_time_offset():
    with open("/tmp/ntp_offset.txt", "r") as f:
        return float(f.readline().strip())

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


def get_angle_4_points(p1: dict, p2: dict, p3: dict, p4: dict) -> Optional[float]:
    """Calculate the angle between two vectors defined by four points.

    Args:
        p1: The first point of the first vector.
        p2: The second point of the first vector.
        p3: The first point of the second vector.
        p4: The second point of the second vector.

    Returns:
        The angle in degrees between the two vectors.
    """
    v1 = (p2['x'] - p1['x'], p2['y'] - p1['y'])
    v2 = (p4['x'] - p3['x'], p4['y'] - p3['y'])

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    magnitude_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0

    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
    angle = math.acos(cos_theta)

    return math.degrees(angle) if not math.isnan(angle) else None

def get_angle_3_points(p1: dict, p2: dict, p3: dict) -> Optional[float]:
    """Calculate the angle between two vectors defined by three points.

    Args:
        p1: The first point of the first vector.
        p2: The point where the two vectors meet.
        p3: The first point of the second vector.

    Returns:
        The angle in degrees between the two vectors.
    """
    
    return get_angle_4_points(p1, p2, p3, p2)

def get_angle_2_points_x_axis(p1: dict, p2: dict) -> Optional[float]:
    """Calculate the angle between a vector defined by two points and the x-axis.

    Args:
        p1: The first point of the vector.
        p2: The second point of the vector.

    Returns:
        The angle in degrees between the vector and the x-axis.
    """

    dx = p2['x'] - p1['x']
    dy = p2['y'] - p1['y']
    angle = math.atan2(dy, dx)
    return math.degrees(angle) if not math.isnan(angle) else None

import numpy as np
import cv2
from typing import List, Tuple, Optional, Union
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates, _BGR_CHANNELS, _VISIBILITY_THRESHOLD, _PRESENCE_THRESHOLD, _BGR_CHANNELS, RED_COLOR, WHITE_COLOR
from typing import Mapping

def new_draw_landmarks(
    image: np.ndarray,
    landmark_list: Optional[List[dict]] = None,
    connections: Optional[List[Tuple[int, int]]] = None,
    landmark_drawing_spec: Optional[
        Union[DrawingSpec, Mapping[int, DrawingSpec]]
    ] = DrawingSpec(color=RED_COLOR),
    connection_drawing_spec: Union[
        DrawingSpec, Mapping[Tuple[int, int], DrawingSpec]
    ] = DrawingSpec(),
    is_drawing_landmarks: bool = True,
):
  """Draws the landmarks and the connections on the image.

  Args:
    image: A three channel BGR image represented as numpy ndarray.
    landmark_list: A landmark list to be annotated on the image.
    connections: A list of landmark index tuples that specifies how landmarks to
      be connected in the drawing.
    landmark_drawing_spec: Either a DrawingSpec object or a mapping from hand
      landmarks to the DrawingSpecs that specifies the landmarks' drawing
      settings such as color, line thickness, and circle radius. If this
      argument is explicitly set to None, no landmarks will be drawn.
    connection_drawing_spec: Either a DrawingSpec object or a mapping from hand
      connections to the DrawingSpecs that specifies the connections' drawing
      settings such as color and line thickness. If this argument is explicitly
      set to None, no landmark connections will be drawn.
    is_drawing_landmarks: Whether to draw landmarks. If set false, skip drawing
      landmarks, only contours will be drawed.

  Raises:
    ValueError: If one of the followings:
      a) If the input image is not three channel BGR.
      b) If any connetions contain invalid landmark index.
  """
  if not landmark_list:
    return
  if image.shape[2] != _BGR_CHANNELS:
    raise ValueError('Input image must contain three channel bgr data.')
  image_rows, image_cols, _ = image.shape
  idx_to_coordinates = {}
  for idx, landmark in enumerate(landmark_list):
    if ((landmark['visibility'] and
         landmark['visibility'] < _VISIBILITY_THRESHOLD) or
        (landmark['presence'] and
         landmark['presence'] < _PRESENCE_THRESHOLD)):
      continue
    landmark_px = _normalized_to_pixel_coordinates(landmark['x'], landmark['y'],
                                                   image_cols, image_rows)
    if landmark_px:
      idx_to_coordinates[idx] = landmark_px
  if connections:
    num_landmarks = len(landmark_list)
    # Draws the connections if the start and end landmarks are both visible.
    for connection in connections:
      start_idx = connection[0]
      end_idx = connection[1]
      if not (0 <= start_idx < num_landmarks and 0 <= end_idx < num_landmarks):
        raise ValueError(f'Landmark index is out of range. Invalid connection '
                         f'from landmark #{start_idx} to landmark #{end_idx}.')
      if start_idx in idx_to_coordinates and end_idx in idx_to_coordinates:
        drawing_spec = connection_drawing_spec[connection] if isinstance(
            connection_drawing_spec, Mapping) else connection_drawing_spec
        cv2.line(image, idx_to_coordinates[start_idx],
                 idx_to_coordinates[end_idx], drawing_spec.color,
                 drawing_spec.thickness)
  # Draws landmark points after finishing the connection lines, which is
  # aesthetically better.
  if is_drawing_landmarks and landmark_drawing_spec:
    for idx, landmark_px in idx_to_coordinates.items():
      drawing_spec = landmark_drawing_spec[idx] if isinstance(
          landmark_drawing_spec, Mapping) else landmark_drawing_spec
      # White circle border
      circle_border_radius = max(drawing_spec.circle_radius + 1,
                                 int(drawing_spec.circle_radius * 1.2))
      cv2.circle(image, landmark_px, circle_border_radius, WHITE_COLOR,
                 drawing_spec.thickness)
      # Fill color into the circle
      cv2.circle(image, landmark_px, drawing_spec.circle_radius,
                 drawing_spec.color, drawing_spec.thickness)
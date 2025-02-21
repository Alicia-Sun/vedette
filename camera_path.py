from matrix_rotation import rotation_matrix_from_rotvec
import math

"""
=======================================================================================================
Camera path classes.
It defines a camera path with a start and end timestep.

To add a new camera path, you need to create a new class deriving from CameraPath and
define the following methods: raw_position, raw_vector_up and raw_focal_point

The position, up vector and focal points will be automatically interpolated if a transition is defined.

The complete animation holds a list of consecutive camera path. The start and end timesteps of
each camera path need to be coherent.
=======================================================================================================
"""

# Global variable defining the orientation of the camera w.r.t the lidar
R_cam_to_lidar = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # identity by default

class CameraPath:
    """ Base class for camera path.
        The following interpolation modes are available:
            - linear
            - square
            - s-shape
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.previous_camera_path = None
        self.transition_duration = 0
        self.transition_mode = "linear"

    def timestep_inside_range(self, t):
        return self.start <= t < self.end

    def set_transition(self, previous_camera_path, duration, mode):
        self.transition_duration = duration
        self.transition_mode = mode
        self.previous_camera_path = previous_camera_path

    def compute_transition_weight(self, step):
        if self.transition_duration == 0:
            return 1.0
        w = max(0.0, min(1.0, (step - self.start) / self.transition_duration))
        if self.transition_mode == "linear":
            return w
        elif self.transition_mode == "square":
            return w * w
        elif self.transition_mode == "s-shape":
            beta = 2
            if w < 1e-5:
                return 0.0
            elif w > 1.0 - 1e-5:
                return 1.0
            else:
                return 1.0 / (1.0 + (w / (1.0 - w)) ** (-beta))
        else:
            print("Invalid transition mode: ", self.transition_mode)
            return 0.0

class ThirdPersonView(CameraPath):
    """ Third person view defined with a position, a focal point
        and an up vector relative to the camera frame """
    def __init__(self, start, end, position=[0.0, 0.0, -2.0], focal_point=[0.0, 0.0, 1.0], up_vector=[0.0, -1.0, 0.0]):
        super().__init__(start, end)
        self.position = position
        self.focal_point = focal_point
        self.up_vector = up_vector
        self.type = "Third Person View"

class FirstPersonView(ThirdPersonView):
    """ Specialized class for first person view """
    def __init__(self, start, end, focal_point=[0.0, 0.0, 1.0], up_vector=[0.0, -1.0, 0.0]):
        super().__init__(start, end, focal_point=focal_point, up_vector=up_vector)
        self.position = [0.0, 0.0, 0.0]
        self.type = "First Person View"

class FixedPositionView(CameraPath):
    """ Fixed absolute position camera. """
    def __init__(self, start, end, position=None, focal_point=None, up_vector=[0.0, 0.0, 1.0]):
        super().__init__(start, end)
        self.position = position
        self.focal_point = focal_point
        self.up_vector = up_vector
        self.type = "Fixed position"

class AbsoluteOrbit(CameraPath):
    """ Absolute orbit defined by a center of rotation (center), a rotation axis (up_vector),
        an initial position (initial_pos) and a focal point (focal_point). """
    def __init__(self, start, end, center, initial_pos, up_vector, focal_point, ccw=1):
        super().__init__(start, end)
        self.center = center
        self.up_vector = [x / math.sqrt(sum(v**2 for v in up_vector)) for x in up_vector]
        self.initial_pos = initial_pos
        self.focal_point = focal_point
        self.ccw = ccw
        self.type = "Absolute Orbit"

class RelativeOrbit(CameraPath):
    """ Relative orbit defined by an initial position relative and an up vector to the camera frame. """
    def __init__(self, start, end, initial_pos, up_vector, ccw=1):
        super().__init__(start, end)
        self.up_vector = [x / math.sqrt(sum(v**2 for v in up_vector)) for x in up_vector]
        self.initial_pos = initial_pos
        self.ccw = ccw
        self.type = "Relative Orbit"

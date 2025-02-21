import math

def rotation_matrix_from_euler(euler_angles, order="xyz", degrees=False):
    """
    Compute a rotation matrix from Euler angles.
    """
    if degrees:
        euler_angles = [math.radians(angle) for angle in euler_angles]

    if len(euler_angles) != 3:
        raise ValueError("euler_angles must have a length of 3.")
    if not isinstance(order, str) or len(order) != 3:
        raise ValueError("order must be a permutation of 'xyz' (e.g., 'xyz', 'zyx').")

    def rotation_matrix_x(theta):
        return [
            [1, 0, 0],
            [0, math.cos(theta), -math.sin(theta)],
            [0, math.sin(theta), math.cos(theta)]
        ]

    def rotation_matrix_y(theta):
        return [
            [math.cos(theta), 0, math.sin(theta)],
            [0, 1, 0],
            [-math.sin(theta), 0, math.cos(theta)]
        ]

    def rotation_matrix_z(theta):
        return [
            [math.cos(theta), -math.sin(theta), 0],
            [math.sin(theta), math.cos(theta), 0],
            [0, 0, 1]
        ]

    axis_to_matrix = {"x": rotation_matrix_x, "y": rotation_matrix_y, "z": rotation_matrix_z}
    rotation_matrix = [[1 if i == j else 0 for j in range(3)] for i in range(3)]

    def matrix_multiply(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    for angle, axis in zip(euler_angles, order.lower()):
        rotation_matrix = matrix_multiply(rotation_matrix, axis_to_matrix[axis](angle))

    return rotation_matrix

def rotation_matrix_from_rotvec(rotvec):
    """
    Compute a rotation matrix from a rotation vector specified in degrees.
    """
    angle_radians = math.sqrt(sum(x**2 for x in rotvec))
    if angle_radians == 0:
        return [[1 if i == j else 0 for j in range(3)] for i in range(3)]
    axis = [x / angle_radians for x in rotvec]
    x, y, z = axis
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    t = 1 - c

    return [
        [t*x*x + c,    t*x*y - z*s,  t*x*z + y*s],
        [t*y*x + z*s,  t*y*y + c,    t*y*z - x*s],
        [t*z*x - y*s,  t*z*y + x*s,  t*z*z + c]
    ]

def rotation_matrix_to_rotvec(rotation_matrix):
    """
    Convert a 3x3 rotation matrix to a rotation vector (rotvec).
    """
    trace = sum(rotation_matrix[i][i] for i in range(3))
    theta = math.acos(max(-1.0, min(1.0, (trace - 1) / 2)))
    if math.isclose(theta, 0.0):
        return [0.0, 0.0, 0.0]
    R = rotation_matrix
    axis = [
        (R[2][1] - R[1][2]) / (2 * math.sin(theta)),
        (R[0][2] - R[2][0]) / (2 * math.sin(theta)),
        (R[1][0] - R[0][1]) / (2 * math.sin(theta))
    ]
    return [theta * a for a in axis]
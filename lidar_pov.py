import paraview.web.venv
import asyncio
from trame.app import get_server, asynchronous
from trame.widgets import iframe, paraview
from paraview import simple
from lidarview import simple as lvsmp
from trame.ui.html import DivLayout
from trame.widgets import paraview
import subprocess

# Global variable to store the SLAM object
slam_object = None

def start_streaming(port):
    """Start the streaming process and return the process object."""
    return subprocess.Popen(["PacketFileSender.exe", "test_data.pcap", "--lidarPort", str(port)])

# Start the initial streaming process on port 2369
streaming_process = start_streaming(2369)

# Initialize the server
server = get_server(client_type="vue2")  # client_type="vue2"
state, ctrl = server.state, server.controller

# Load LiDAR data
stream = lvsmp.OpenSensorStream("VLP-16", "Velodyne", ListeningPort=2369)
stream.Start()

representation = simple.Show(stream)
view = simple.GetRenderView()

# Set up the render view
view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]  # Black background
view.OrientationAxesVisibility = 0
view = simple.Render()
view = simple.GetActiveView()
state.slam = None

# -----------------------------------------------------------------------------
# Set Camera Position and Orientation
# -----------------------------------------------------------------------------

import numpy as np
from matrix_rotation import rotation_matrix_from_euler
def quaternion_to_rotation_matrix(q):
    """
    Convert a quaternion [x, y, z, w] into a 3x3 rotation matrix.
    """
    x, y, z, w = q
    return [
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
    ]

def matrix_vector_multiply(matrix, vector):
    """
    Multiply a 3x3 matrix by a 3-element vector.
    """
    return [
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
        matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]
    ]

# REQUIRES SLAM RUNNING TO RUN
def set_camera_to_lidar():
    """
    Set the camera position and focal point to match the LiDAR's position and orientation
    using the SLAM trajectory or pose data. This creates a first-person view from the LiDAR's perspective.
    """
    print('Setting camera to LiDAR position and orientation.')
    camera = view.GetActiveCamera()

    if not state.slam:
        print("SLAM is not initialized. Cannot set camera position.")
        return

    # Get the SLAM filter's output (trajectory or pose data)
    slam_filter = state.slam.GetClientSideObject()
    trajectory = slam_filter.GetOutput(1)  # Assuming trajectory is on output port 1

    # Get the last pose from the trajectory
    num_points = trajectory.GetNumberOfPoints()
    if num_points == 0:
        print("No trajectory data available.")
        return

    # Extract the last position and orientation from the trajectory
    last_position = trajectory.GetPoint(num_points - 1)
    last_orientation = trajectory.GetPointData().GetArray("Orientation(Quaternion)").GetTuple(num_points - 1)

    print("Last position:", last_position)
    print("Last orientation (quaternion):", last_orientation)

    # Define the "front" direction of the LiDAR puck
    # Assuming the LiDAR's front is along the positive X-axis in its local coordinate system
    front_direction = [1, 0, 0]  # Adjust this if the front direction is different

    # Define the up vector in the LiDAR's local coordinate system
    up_vector = [0, 0, 1]  # Z-axis is up

    # Convert the quaternion orientation to a rotation matrix
    rotation_matrix = quaternion_to_rotation_matrix(last_orientation)

    # Rotate the front direction and up vector based on the LiDAR's orientation
    front_direction = matrix_vector_multiply(rotation_matrix, front_direction)
    up_vector = matrix_vector_multiply(rotation_matrix, up_vector)

    # Define the camera position at the LiDAR's position
    camera_position = last_position

    # Define the focal point slightly in front of the LiDAR
    focal_point = [
        last_position[0] + front_direction[0],
        last_position[1] + front_direction[1],
        last_position[2] + front_direction[2]
    ]

    # Apply the camera settings
    camera.SetFocalPoint(focal_point[0], focal_point[1], focal_point[2])
    camera.SetPosition(camera_position[0], camera_position[1], camera_position[2])
    camera.SetViewUp(up_vector[0], up_vector[1], up_vector[2])

    # Set a narrow field of view for a first-person perspective
    camera.SetViewAngle(30)  # Adjust this value to control the zoom (smaller = more zoomed in)

    # Adjust the clipping range to only show nearby points
    # near_clip = 0.1  # Minimum distance to render (adjust as needed)
    # far_clip = 1  # Maximum distance to render (adjust as needed)
    # camera.SetClippingRange(near_clip, far_clip)

    # Force the view to update
    view.Update()
    simple.Render()

    # Debugging: Print camera settings
    # print("Camera Position:", camera.GetPosition())
    # print("Camera Focal Point:", camera.GetFocalPoint())
    # print("Camera View Up:", camera.GetViewUp())
    # print("Camera Clipping Range:", camera.GetClippingRange())


# -----------------------------------------------------------------------------
# Color Scheme
# -----------------------------------------------------------------------------

def create_color_template(template_name):
    lut = simple.GetColorTransferFunction(template_name)
    if template_name == "intensity":
        lut.RGBPoints = [
            0.0, 0.0, 0.0, 1.0,   # Blue
            40.0, 1.0, 1.0, 0.0,  # Yellow
            100.0, 1.0, 0.0, 0.0  # Red
        ]
        lut.ColorSpace = 'HSV'
    elif template_name == "cyan_pink":
        lut.RGBPoints = [
            0.0, 0.0, 1.0, 1.0,   # Cyan
            100.0, 1.0, 0.0, 1.0  # Pink
        ]
        lut.ColorSpace = 'HSV'
    elif template_name == "red":
        lut.RGBPoints = [
            0.0, 1.0, 0.6, 0.6,   # Light Red
            100.0, 0.502, 0.0, 0.0  # Dark Red
        ]
        lut.ColorSpace = 'HSV'
    elif template_name == "blue":
        lut.RGBPoints = [
            0.0, 0.4, 0.8, 1.0,   # Light Blue
            100.0, 0.0, 0.0, 0.6  # Dark Blue
        ]
        lut.ColorSpace = 'HSV'
    elif template_name == "yellow":
        lut.RGBPoints = [
            0.0, 1.0, 1.0, 0.8,   # Light Yellow
            100.0, 0.8, 0.6, 0.0  # Dark Yellow
        ]
        lut.ColorSpace = 'HSV'
    return lut

def apply_color_template(color_template, **kwargs):
    print(f'Applying template: {color_template}')
    lut = create_color_template(color_template)
    simple.ColorBy(representation, ('POINTS', 'intensity'))
    representation.LookupTable = lut
    view.Update()
    simple.Render()
    ctrl.view_update()

state.color_template = "cyan_pink"
state.change("color_template")(apply_color_template)



# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

state.loop_pcap = True
state.counter = 0

@state.change("play")
@asynchronous.task
async def update_play(**kwargs):
    print("calling update to play")
    while state.play:
        if lvsmp.RefreshStream(stream):
            if state.counter < 20:
                set_camera_to_lidar()
                state.counter += 1
            # set_camera_to_lidar()
            ctrl.view_update_image()
            ctrl.view_update_geometry()
        await asyncio.sleep(0.1)

def on_slam_start():
    print("starting slam")
    if state.slam:
        return
    state.slam = simple.SLAMonline(PointCloud=stream)
    simple.Hide(stream, view)
    for i in range(0, 7):
        slamDisplay = simple.Show(simple.OutputPort(state.slam, i), view)
        slamDisplay.Representation = 'Surface'

    view.Update()
    simple.SetActiveSource(state.slam)

def on_slam_reset():
    state.slam.Resetstate()

# -----------------------------------------------------------------------------
# Point Sizes
# -----------------------------------------------------------------------------

state.point_size = 3
def update_point_size(point_size, **kwargs):
    size_mapping = {1: 1, 2: 1.5, 3: 2, 4: 3.5, 5: 4.5, 6: 6, 7: 7}
    actual_size = size_mapping.get(point_size, 5)  # Default to 5

    representation.PointSize = actual_size
    view.Update()
    simple.Render()
    ctrl.view_update()

state.change("point_size")(update_point_size)
on_slam_start()

# -----------------------------------------------------------------------------
# GUI Setup
# -----------------------------------------------------------------------------

state.play = True

with DivLayout(server) as layout:
    layout.toolbar = None
    layout.icon = None
    layout.title = None
    layout.footer = None
    iframe.Communicator(target_origin="http://localhost:3000", enable_rpc=True)

    html_view = paraview.VtkRemoteLocalView(
        view,
        namespace="view",
        style="height: 100vh; width: 100vw; margin: 0px; position: relative;"
    )
    ctrl.view_update = html_view.update
    ctrl.view_update_geometry = html_view.update_geometry
    ctrl.view_update_image = html_view.update_image
    ctrl.view_reset_camera = html_view.reset_camera

if __name__ == "__main__":
    server.start(port=9000)
    print('after start')
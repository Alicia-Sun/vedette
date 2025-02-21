import asyncio
import paraview.simple as smp

# hardcoded import
from matrix_rotation import rotation_matrix_from_euler
import camera_path as cp
import temporal_animation_cue_helpers as tach

from trame.app import get_server
from trame.widgets import iframe, paraview
from trame.ui.html import DivLayout

# Initialize server
server = get_server()
state, ctrl = server.state, server.controller

# Third-person view, relative to current SLAM pose
position = [0, 0, 0]
focal_point = [0, 1, 0]
up_vector = [0, 1, 1]
cp.R_cam_to_lidar = rotation_matrix_from_euler([0, 0, 0], 'xyz', degrees=True)

# Use last pose of the selected trajectory
tach.params['trajectory_time_array'] = None
tach.params['verbose'] = False

# Load LiDAR data
inputfile = 'C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/test_data.pcap'
stream = smp.OpenPCAP(inputfile, "VLP-16", "Velodyne")
view = smp.GetRenderView()
representation = smp.Show(stream, view)

# Set up render view
view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]
view.OrientationAxesVisibility = 0
smp.Render()

# Camera setup
def start_cue():
    tach.start_cue_generic_setup()
    src = smp.GetActiveSource().GetClientSideObject()
    trajectory_output = src.GetOutput(1 if src.GetClassName() == 'vtkSlam' else 0)
    camera = cp.ThirdPersonView(0, float('inf'), position=position, focal_point=focal_point, up_vector=up_vector)
    return trajectory_output, camera

def update_camera():
    trajectory_output, camera = start_cue()
    view.CameraPosition = camera.position
    view.CameraFocalPoint = camera.focal_point
    view.CameraViewUp = camera.up_vector
    view.Update()
    smp.Render()
    ctrl.view_update()

state.change("play")(update_camera)

# GUI Setup
with DivLayout(server) as layout:
    iframe.Communicator(target_origin="http://localhost:3000", enable_rpc=True)
    html_view = paraview.VtkRemoteLocalView(
        view,
        namespace="view",
        style="height: 100vh; width: 100vw; margin: 0px; position: relative;"
    )
    ctrl.view_update = html_view.update

if __name__ == "__main__":
    server.start()

import paraview.web.venv
import asyncio

from trame.app import get_server, asynchronous
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageLayout

from paraview import simple
from lidarview import simple as lvsmp
import math

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# ParaView code for PCAP processing only
# -----------------------------------------------------------------------------

# Setup color mapping based on intensity
intensityLUT = simple.GetColorTransferFunction('intensity')
intensityLUT.RGBPoints = [0.0, 0.0, 0.0, 1.0, 40.0, 1.0, 1.0, 0.0, 100.0, 1.0, 0.0, 0.0]
intensityLUT.ColorSpace = 'HSV'

# Input PCAP file path for LiDAR data
inputfile = 'C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/trame_app/test_data.pcap'

# Load PCAP file (no live sensor stream)
# stream = lvsmp.OpenPCAP(inputfile, "VLP-16", "Velodyne")
stream = lvsmp.OpenSensorStream("VLP-16", "Velodyne")
stream.Start()

# Show the point cloud in the ParaView view
representation = simple.Show(stream)
simple.ColorBy(representation, ('POINTS', 'intensity'))

# Customize the render view
view = simple.GetRenderView()
view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.2]
view.OrientationAxesVisibility = 0
view = simple.Render()
state.slam = None

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

@state.change("play")
@asynchronous.task
async def update_play(**kwargs):
    while state.play:
        try:
            # Commenting out RefreshStream to prevent AttributeError
            # if lvsmp.RefreshStream(stream):
            ctrl.view_update_image()
            ctrl.view_update_geometry()
            await asyncio.sleep(0.1)
        except ConnectionResetError as e:
            print(f"Connection reset: {e}")
            break

def on_slam_start():
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

def show_point_info(event):
    x, y, z = event.point_coords  # Get the clicked point coordinates
    state.point_info = f"X: {x}, Y: {y}, Z: {z}, Intensity: {event.intensity}"

# Function to control the camera for preset views
def set_camera(view_direction):
    view = simple.GetRenderView()  # Get the active render view
    if view_direction == "top":
        # Set the camera position above the scene (looking down along the Z-axis)
        view.CameraPosition = [0, 0, 100]  # Position the camera above the point cloud
        view.CameraFocalPoint = [0, 0, 0]  # Point the camera towards the origin
        view.CameraViewUp = [0, 1, 0]      # Define the "up" direction (Y-axis)
    elif view_direction == "side":
        # Set the side view (along X-axis)
        view.CameraPosition = [100, 0, 0]
        view.CameraFocalPoint = [0, 0, 0]
        view.CameraViewUp = [0, 0, 1]      # Define the "up" direction (Z-axis)
    elif view_direction == "front":
        # Set the front view (along Y-axis)
        view.CameraPosition = [0, 100, 0]
        view.CameraFocalPoint = [0, 0, 0]
        view.CameraViewUp = [0, 0, 1]      # Define the "up" direction (Z-axis)

    view.ResetCamera()  # Adjust the camera to fit the data into the view
    view.StillRender()  # Force a render after setting the camera


# Function to rotate the camera around the point cloud
async def rotate_camera():
    view = simple.GetRenderView()  # Get the active render view
    center = view.CameraFocalPoint  # The center point around which the camera will rotate
    radius = 100  # Distance from the center (adjust as needed based on your scene)
    
    # Rotate the camera in small steps for smooth motion
    for angle in range(0, 360, 5):  # Rotate in steps of 5 degrees
        radians = math.radians(angle)
        
        # Compute new camera position for each angle (circular path)
        new_x = center[0] + radius * math.cos(radians)
        new_y = center[1] + radius * math.sin(radians)
        new_z = view.CameraPosition[2]  # Keep the same height (Z-axis)
        
        # Set the new camera position
        view.CameraPosition = [new_x, new_y, new_z]
        
        # Keep the camera focused on the center of the scene
        view.CameraFocalPoint = center
        
        # Update the view after changing the camera position
        view.StillRender()
        
        # Pause briefly to create the effect of smooth rotation
        await asyncio.sleep(0.05)  # Adjust sleep time for faster/slower rotation

# PCAP Playback functions (Rewind and Pause)
def rewind_pcap():
    lvsmp.Rewind(stream)

def play_animation():
    while state.play:
        lvsmp.NextFrame(stream)
        ctrl.view_update_geometry()
        asyncio.sleep(0.1)

import os
from datetime import datetime

async def export_image():
    # Define the export directory within the current working directory
    export_dir = os.path.join(os.getcwd(), "LiDAR_Exports")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    # Create a unique filename based on the current timestamp
    filename = f"lidar_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(export_dir, filename)

    # Ensure the view is fully rendered before taking the screenshot
    view = simple.GetRenderView()  # Get the current active render view
    simple.SetActiveView(view)
    view.StillRender()  # Force the view to render
    
    # Save the screenshot asynchronously (simulate as async to prevent blocking)
    await asyncio.to_thread(simple.SaveScreenshot, filepath, view=view)
    
    print(f"Screenshot saved to: {filepath}")

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

state.trame__title = "LidarView"

with SinglePageLayout(server) as layout:
    layout.title.set_text("LiDAR Stream")
    layout.icon.click = ctrl.view_reset_camera

    with layout.toolbar:
        vuetify.VSpacer()

        vuetify.VCheckbox(
            v_model=("play", True),
            off_icon="mdi-play",
            on_icon="mdi-stop",
            hide_details=True,
            dense=True,
            classes="mx-2",
        )

        vuetify.VBtn(
            "Start a Slam",
            click=on_slam_start,
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Reset Slam",
            click=on_slam_reset,
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Export as Image",
            click=export_image,
            color="secondary",
            outlined=True,
        )

        vuetify.VBtn(
            "Top View",
            click=lambda: set_camera("top"),
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Side View",
            click=lambda: set_camera("side"),
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Front View",
            click=lambda: set_camera("front"),
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Rotate 360",
            click=lambda: rotate_camera(),
            color="secondary",
            outlined=True,
        )

        vuetify.VBtn(
            "Rewind",
            click=rewind_pcap,
            color="primary",
            outlined=True,
        )

        vuetify.VProgressLinear(
            indeterminate=True,
            absolute=True,
            bottom=True,
            active=("trame__busy",),
        )

    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
            html_view = paraview.VtkRemoteLocalView(view, namespace="view")
            ctrl.view_update = html_view.update
            ctrl.view_update_geometry = html_view.update_geometry
            ctrl.view_update_image = html_view.update_image
            ctrl.view_reset_camera = html_view.reset_camera

# -----------------------------------------------------------------------------
# Point Manipulation and Heatmap Tools
# -----------------------------------------------------------------------------

with layout.toolbar:
    vuetify.VSlider(
        v_model=("intensity_min", 0),
        min=0, max=100, step=1,
        label="Min Intensity",
        dense=True,
    )
    
    vuetify.VSlider(
        v_model=("intensity_max", 100),
        min=0, max=100, step=1,
        label="Max Intensity",
        dense=True,
    )

    vuetify.VBtn(
        "Intensity Heatmap",
        click=lambda: simple.ColorBy(representation, ('POINTS', 'intensity')),
        color="primary",
        outlined=True,
    )

    vuetify.VBtn(
        "Distance Heatmap",
        click=lambda: simple.ColorBy(representation, ('POINTS', 'distance')),
        color="secondary",
        outlined=True,
    )

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

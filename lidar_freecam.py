import paraview.web.venv
import asyncio
from trame.app import get_server, asynchronous
from trame.widgets import iframe, paraview
from paraview import simple
from lidarview import simple as lvsmp
from trame.ui.html import DivLayout
from trame.widgets import paraview
import subprocess

slam_object = None


def start_streaming(port):
    """Start the streaming process and return the process object."""
    return subprocess.Popen(["PacketFileSender.exe", "test_data.pcap", "--loop", "--lidarPort", str(port)])

streaming_process = start_streaming(2368)

# Initialize the server
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# Load LiDAR data
# inputfile = 'C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/test_data.pcap'
# stream = lvsmp.OpenPCAP(inputfile, "VLP-16", "Velodyne")
stream = lvsmp.OpenSensorStream("VLP-16", "Velodyne", ListeningPort=2368)
stream.Start()

# representation = simple.Show(stream)  # Hiding the original points
view = simple.GetRenderView()

sphere = simple.Sphere(
         Radius=0.25,
         ThetaResolution=6,
         PhiResolution=6,
     )
glyph = simple.Glyph(Input=stream, GlyphType=sphere)
glyph.GlyphMode = 'Every Nth Point' # 'All Points'
glyph.Stride = 6
glyph.GlyphType.Radius = 0.1
representation = simple.Show(glyph, view)
representation.Diffuse = 0.9 
representation.Ambient = 1.0
simple.Hide(stream, view)

view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]  # Black background
view.OrientationAxesVisibility = 0
view = simple.Render()
state.slam = None

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
    print('hellooo')
    """
    Apply a color scheme to the point cloud visualization.

    Args:
        template_name (str): Name of the color template.
    """
    print(f'Applying template: {color_template}')
    
    lut = create_color_template(color_template)
    simple.ColorBy(representation, ('POINTS', 'intensity'))
    representation.LookupTable = lut
    if state.slam:
        for i in range(0, 7):
            slam_display = simple.Show(simple.OutputPort(state.slam, i), view)
            simple.ColorBy(slam_display, ('POINTS', 'intensity'))
            slam_display.LookupTable = lut

    view.Update()
    simple.Render()
    ctrl.view_update()

state.color_template = "cyan_pink"
state.change("color_template")(apply_color_template)


# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

@state.change("play")
@asynchronous.task
async def update_play(**kwargs):
    while state.play:
        if lvsmp.RefreshStream(stream):
            ctrl.view_update_image()
            ctrl.view_update_geometry()
        await asyncio.sleep(0.1)

@state.change("slam_status")
def on_slam_start(slam_status, **kwargs):
    if slam_status:
        print("Starting SLAM")
        if state.slam:
            return
        state.slam = simple.SLAMonline(PointCloud=stream)
        simple.Hide(stream, view)
        lut = create_color_template(state.color_template)
        for i in range(0, 7):
            slamDisplay = simple.Show(simple.OutputPort(state.slam, i), view)
            # slamDisplay.Representation = 'intensity'
            simple.ColorBy(slamDisplay, ('POINTS', 'intensity'))
            slamDisplay.LookupTable = lut
            
        view.Update()
        simple.SetActiveSource(state.slam)
    else:
        print("SLAM is already running or not started")
    # print("starting slam")
    # if state.slam:
    #     return
    # state.slam = simple.SLAMonline(PointCloud=stream)
    # simple.Hide(stream, view)
    # for i in range(0, 7):
    #     slamDisplay = simple.Show(simple.OutputPort(state.slam, i), view)
    #     slamDisplay.Representation = 'Surface'

    # view.Update()
    # simple.SetActiveSource(state.slam)

def on_slam_reset():
    state.slam.Resetstate()

state.slam_status = False
# state.change("slam_status")(on_slam_start)

# -----------------------------------------------------------------------------
# Point Sizes
# -----------------------------------------------------------------------------

state.point_size = 3

def update_point_size(point_size, **kwargs):
    """
    Update the point size in the ParaView representation.

    Args:
        point_size (int): The current value from the slider (1-7).
    """
    size_mapping = {1: 0.02, 2: 0.04, 3: 0.06, 4: 0.1, 5: 0.15, 6: 0.2, 7: 0.25}
    actual_size = size_mapping.get(point_size, 0.1)
    
    glyph.GlyphType.Radius = actual_size
    view.Update()
    simple.Render()
    ctrl.view_update()


# USING ORIGINAL POINTS INSTEAD OF GLYPHS
# state.point_size = 3

# def update_point_size(point_size, **kwargs):
#     """
#     Update the point size in the ParaView representation.

#     Args:
#         point_size (int): The current value from the slider (1-7).
#     """
#     size_mapping = {1: 1, 2: 1.5, 3: 2, 4: 3.5, 5: 4.5, 6: 6, 7: 7}
#     actual_size = size_mapping.get(point_size, 5)  # Default to 5

#     representation.PointSize = actual_size
#     view.Update()
#     simple.Render()
#     ctrl.view_update()

state.change("point_size")(update_point_size)


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
    server.start(port=8080)
   

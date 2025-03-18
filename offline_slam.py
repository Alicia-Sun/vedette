import paraview.web.venv
import asyncio
import os

from trame.app import get_server, asynchronous
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageLayout

from paraview import simple
from lidarview import simple as lvsmp
import pipeline_setup_helpers as helpers

# -----------------------------------------------------------------------------
# trame setup
# -----------------------------------------------------------------------------

server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# ParaView code
# -----------------------------------------------------------------------------

state.pcap_file = "C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/test_data.pcap"
state.slam = None

view = helpers.setup_view(use_gradient=True, background=[0.0, 0.0, 0.2])

def load_pcap_file():
    print("cp1")
    if not state.pcap_file or not os.path.exists(state.pcap_file):
        print("Invalid .pcap file")
        return
    
    lidar_reader = helpers.load_lidar_frames(state.pcap_file)
    print("cp2")
    simple.Show(lidar_reader, view)
    view.Update()
    print("cp3")
    state.lidar_reader = lidar_reader

def on_slam_start():
    if state.slam:
        return
    
    if not hasattr(state, "lidar_reader"):
        print("No LiDAR data loaded.")
        return
    
    state.slam = simple.SLAMoffline(PointCloud=state.lidar_reader)
    simple.Hide(state.lidar_reader, view)
    
    for i in range(7):
        slam_display = simple.Show(simple.OutputPort(state.slam, i), view)
        slam_display.Representation = 'Surface'
    
    view.Update()
    simple.SetActiveSource(state.slam)

def on_slam_reset():
    if state.slam:
        state.slam.Resetstate()
    
# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

state.trame__title = "PCAP LiDAR SLAM"

load_pcap_file()
with SinglePageLayout(server) as layout:
    layout.title.set_text("LiDAR PCAP Viewer")
    layout.icon.click = ctrl.view_reset_camera

    with layout.toolbar:
        vuetify.VSpacer()
        
        vuetify.VBtn(
            "Load PCAP",
            click=load_pcap_file,
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Start SLAM",
            click=on_slam_start,
            color="primary",
            outlined=True,
        )

        vuetify.VBtn(
            "Reset SLAM",
            click=on_slam_reset,
            color="primary",
            outlined=True,
        )

        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-crop-free")

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
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

import paraview.web.venv
import asyncio
import numpy as np
import time
import plotly.graph_objects as go  # Import Plotly Graph Objects

from trame.app import get_server, asynchronous
from trame.widgets import vuetify, paraview  # Import Vuetify and ParaView widgets
from trame_leaflet.widgets.leaflet import LMap, LTileLayer, LMarker  # Import Leaflet widgets
from trame_plotly.widgets.plotly import Figure  # Import Plotly Figure widget
from trame.ui.vuetify import SinglePageLayout, VAppLayout


from paraview import simple
from lidarview import simple as lvsmp
from vtkmodules.vtkFiltersSources import vtkCubeSource
from paraview.vtk.util.numpy_support import vtk_to_numpy
from paraview.simple import servermanager
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import open3d as o3d
import hdbscan
from trame.widgets.html import Html
from trame.widgets import vuetify, html


# -----------------------------------------------------------------------------
# Trame Setup
# -----------------------------------------------------------------------------

server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# ParaView Setup
# -----------------------------------------------------------------------------

# Function to create LUTs for different color templates
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


# intensityLUT = simple.GetColorTransferFunction('intensity')
# intensityLUT.RGBPoints = [
#     0.0, 0.0, 0.0, 1.0,
#     40.0, 1.0, 1.0, 0.0,
#     100.0, 1.0, 0.0, 0.0
# ]
# intensityLUT.ColorSpace = 'HSV'

inputfile = 'C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/trame_app/test_data.pcap'
stream = lvsmp.OpenPCAP(inputfile, "VLP-16", "Velodyne")

# stream = lvsmp.OpenSensorStream("VLP-16", "Velodyne")
# stream.Start()

representation = simple.Show(stream)
# colors = ['intensity']
# simple.ColorBy(representation, ('POINTS', 'intensity'))

view = simple.GetRenderView()


# Function to apply a color template
def apply_color_template(template_name, view):
    print('Applying template:', template_name)

    lut = create_color_template(template_name)
    simple.ColorBy(representation, ('POINTS', 'intensity'))
    representation.LookupTable = lut

    view.Update()
    view.UseColorPaletteForBackground = 0
    view.Background = [0.0, 0.0, 0.0]
    view.OrientationAxesVisibility = 0
    view = simple.Render()
    ctrl.view_update()


# apply_color_template("cyan_pink", view)
view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]
view.OrientationAxesVisibility = 0
view = simple.Render()
state.slam = None

# -----------------------------------------------------------------------------
# Bounding Boxes with Open3D
# -----------------------------------------------------------------------------

# List to store bounding box displays
bounding_box_displays = []
state.bounding_boxes_visible = False  # Initial visibility

def calculate_adaptive_eps(points, factor=0.05):
    """
    Calculate adaptive `eps` based on average point spacing.
    """
    distances = np.linalg.norm(points - points.mean(axis=0), axis=1)
    avg_distance = np.mean(distances)
    return avg_distance * factor

def render_bounding_boxes(bounding_boxes, view):
    """
    Render a list of bounding boxes in the specified ParaView view.
    Each bounding box should have 'min_bound' and 'max_bound' as (x, y, z) tuples.
    """
    for box in bounding_boxes:
        min_bound = box["min_bound"]
        max_bound = box["max_bound"]

        # Use ProgrammableSource to define bounds dynamically
        programmable_source = simple.ProgrammableSource()
        programmable_source.OutputDataSetType = "vtkPolyData"
        programmable_source.Script = f"""
import vtk
cube = vtk.vtkCubeSource()
cube.SetBounds({min_bound[0]}, {max_bound[0]}, {min_bound[1]}, {max_bound[1]}, {min_bound[2]}, {max_bound[2]})
cube.Update()
output.ShallowCopy(cube.GetOutput())
"""

        # Display the bounding box in the view
        display = simple.Show(programmable_source, view)
        display.Representation = 'Wireframe'
        display.DiffuseColor = [1, 0, 0]  # Red color for visibility
        display.LineWidth = 2  # Optional: Set line width for better visibility

        # Store the display and the source in bounding_box_displays
        bounding_box_displays.append((display, programmable_source))

    view.Update()

def downsample_points(points, voxel_size=0.1):
    """
    Downsample a point cloud using a voxel grid implemented with NumPy.
    Args:
        points (numpy.ndarray): Original points as a NumPy array.
        voxel_size (float): Size of the voxel grid in meters.

    Returns:
        numpy.ndarray: Downsampled points as a NumPy array.
    """
    # Ensure points array is valid
    if points.shape[1] > 3:
        points = points[:, :3]  # Retain only XYZ coordinates
    points = points.astype(np.float32)  # Ensure float32 data type
    points = points[~np.isnan(points).any(axis=1)]  # Remove NaNs
    points = points[~np.isinf(points).any(axis=1)]  # Remove Inf values

    # Shift points to positive space
    min_bounds = points.min(axis=0)
    shifted_points = points - min_bounds

    # Quantize points into voxel grid
    voxel_indices = (shifted_points / voxel_size).astype(np.int32)

    # Create a dictionary to store unique voxels
    voxel_dict = {}
    for i, voxel in enumerate(voxel_indices):
        key = tuple(voxel)  # Use voxel indices as dictionary keys
        if key not in voxel_dict:
            voxel_dict[key] = points[i]  # Store the first point in the voxel

    # Extract downsampled points from the dictionary
    downsampled_points = np.array(list(voxel_dict.values()))

    return downsampled_points


def add_bounding_boxes(stream, view, eps=0.3, min_samples=5, voxel_size=0.1):
    """
    Extract points from the stream, downsample, perform clustering, and render bounding boxes.
    """
    # Extract points from the stream
    point_cloud_data = servermanager.Fetch(stream)
    vtk_points = point_cloud_data.GetPoints().GetData()
    points = vtk_to_numpy(vtk_points)
    print(points)

    # Downsample the points 
    points = downsample_points(points, voxel_size)

    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(points)
    labels = clustering.labels_

    # Prepare bounding boxes based on clusters
    bounding_boxes = []
    for label in set(labels):
        if label == -1:
            continue  # Skip noise points

        # Get points in the current cluster
        cluster_points = points[labels == label]

        # Calculate min and max bounds for the bounding box
        min_bound = cluster_points.min(axis=0)
        max_bound = cluster_points.max(axis=0)

        # Append bounding box information
        bounding_boxes.append({
            "min_bound": min_bound,
            "max_bound": max_bound,
        })

    # Render bounding boxes in the ParaView view
    render_bounding_boxes(bounding_boxes, view)

# Function to toggle bounding boxes
def toggle_bounding_boxes():
    """
    Toggle the visibility of bounding boxes.
    """
    # Check if bounding boxes have been added yet
    if not bounding_box_displays:
        # If not, generate bounding boxes
        add_bounding_boxes(stream, view)
        state.bounding_boxes_visible = True
    else:
        # Toggle visibility
        state.bounding_boxes_visible = not state.bounding_boxes_visible
        visibility = 1 if state.bounding_boxes_visible else 0
        for display, source in bounding_box_displays:
            display.Visibility = visibility
        view.Update()

# Bind the function to the controller
ctrl.toggle_bounding_boxes = toggle_bounding_boxes

# Removed the initial call to add_bounding_boxes(stream, view) to prevent bounding boxes from showing at startup

# -----------------------------------------------------------------------------
# Point Sizes
# -----------------------------------------------------------------------------

state.point_size = 3

def update_point_size(point_size, **kwargs):
    """
    Update the point size in the ParaView representation based on the slider value.

    Args:
        point_size (int): The current value from the slider (1-7).
        **kwargs: Arbitrary keyword arguments (ignored).
    """
    # Define a mapping from slider value to actual point sizes
    size_mapping = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13}
    actual_size = size_mapping.get(point_size, 5)  # Default to 5 if out of range

    # Update the ParaView representation's PointSize
    representation.PointSize = actual_size
    view.Update()
    ctrl.view_update()


# Bind the callback to changes in 'point_size'
state.change("point_size")(update_point_size)



# -----------------------------------------------------------------------------
# Checkpoint Management
# -----------------------------------------------------------------------------

checkpoint_markers = []
state.checkpoint_labels = []  # List to store checkpoint positions
state.selected_checkpoint = 0

def add_checkpoint():
    """
    Function to add a checkpoint marker based on the drone's current position during SLAM.
    """
    # Get the current drone position from the SLAM process
    if state.slam is not None:
        position = state.slam.get_current_position()  # Fetch `[x, y, z]` position
    else:
        print("SLAM process is not running.")
        return

    # Add the checkpoint position to the list
    checkpoint_markers.append(position)

    # Update the dropdown labels in state
    state.checkpoint_labels = [f"Checkpoint {i}" for i in range(len(checkpoint_markers))]

    # Render checkpoint marker in ParaView
    programmable_source = simple.ProgrammableSource()
    programmable_source.OutputDataSetType = "vtkPolyData"
    programmable_source.Script = f"""
import vtk
sphere = vtk.vtkSphereSource()
sphere.SetCenter({position[0]}, {position[1]}, {position[2]})
sphere.SetRadius(20)  # Adjust marker size as needed
sphere.Update()
output.ShallowCopy(sphere.GetOutput())
"""

    # Show marker in the view
    display = simple.Show(programmable_source, view)
    display.Representation = 'Surface'
    display.DiffuseColor = [0, 1, 0]  # Green color for checkpoint marker
    view.Update()

ctrl.add_checkpoint = add_checkpoint

def navigate_to_checkpoint(checkpoint_index):
    """
    Navigate the drone to the selected checkpoint.
    """
    print(checkpoint_markers)
    if checkpoint_index < 0 or checkpoint_index >= len(checkpoint_markers):
        print("Invalid checkpoint index")
        return

    checkpoint = checkpoint_markers[checkpoint_index]

    # Example: Send navigation commands to the drone
    print(f"Navigating to checkpoint: {checkpoint}")

    # Example: Use a drone control library like DroneKit
    # drone.simple_goto(LocationGlobalRelative(checkpoint[0], checkpoint[1], checkpoint[2]))

ctrl.navigate_to_checkpoint = navigate_to_checkpoint

# -----------------------------------------------------------------------------
# Bird's-Eye View and Screenshot
# -----------------------------------------------------------------------------
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

def set_birds_eye_view():
    """
    Adjust the camera to show a bird's-eye view (top-down).
    """
    set_camera("top")

def save_screenshot():
    """
    Capture and save the current screen view as a PNG file.
    """
    file_path = f"screenshot_{int(time.time())}.png"
    simple.WriteImage(file_path)
    print(f"Screenshot saved to {file_path}")

# Bind the functions to the controller
ctrl.set_birds_eye_view = set_birds_eye_view
ctrl.save_screenshot = save_screenshot

# -----------------------------------------------------------------------------
# Drone Position and Altitude Simulation
# -----------------------------------------------------------------------------

# Initialize state variables
state.drone_position = [37.7749, -122.4194]  # Starting position (latitude, longitude)
state.altitude_data = []  # List to store altitude over time

# Initialize the Plotly figure as a go.Figure object
state.altitude_figure = go.Figure(
    data=[
        go.Scatter(
            x=['2020-10-04', '2021-11-04', '2023-12-04'],
            y=[90, 40, 60],
            mode='lines+markers',
            name='Altitude'
        )
    ],
    layout=go.Layout(
        title="Drone Altitude Over Time",
        xaxis=dict(title="Time (s)"),
        yaxis=dict(title="Altitude (m)"),
        margin=dict(l=50, r=10, t=50, b=40),
    )
)

def update_altitude_figure():
    """
    Update the altitude Plotly figure with new data.
    """
    times = [t for t, a in state.altitude_data]
    altitudes = [a for t, a in state.altitude_data]

    # Create a new Plotly Figure object with updated data
    fig = go.Figure(
        data=[
            go.Scatter(
                x=times,
                y=altitudes,
                mode='lines+markers',
                name='Altitude'
            )
        ],
        layout=go.Layout(
            title='Drone Altitude Over Time',
            xaxis=dict(title='Time (s)'),
            yaxis=dict(title='Altitude (m)'),
            margin=dict(l=50, r=10, t=50, b=40),
        )
    )

    # Update the state with the new figure
    state.altitude_figure = fig
    state.dirty("altitude_figure")  # Trigger UI update

@asynchronous.task
async def update_drone_data():
    """
    Asynchronous task to simulate drone position and altitude updates.
    """
    start_time = time.time()
    while True:
        # Simulate drone position and altitude
        current_time = time.time() - start_time
        # Simulate position (latitude, longitude)
        lat = 37.7749 + 0.0001 * current_time  # Simulated movement
        lon = -122.4194 + 0.0001 * current_time
        state.drone_position = [lat, lon]
        # Simulate altitude
        altitude = 100 + 10 * np.sin(current_time / 10.0)
        state.altitude_data.append((current_time, altitude))
        # Keep the last 100 data points
        state.altitude_data = state.altitude_data[-100:]
        # Update the Plotly figure
        update_altitude_figure()
        await asyncio.sleep(1)  # Update every second

# Start updating drone data
update_drone_data()

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

@state.change("play")
@asynchronous.task
async def update_play(**kwargs):
    pass  # Placeholder for play/pause functionality

def on_slam_start():
    """
    Start the SLAM process.
    """
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
    """
    Reset the SLAM process.
    """
    state.slam.Resetstate()

# -----------------------------------------------------------------------------
# GUI Setup
# -----------------------------------------------------------------------------

state.trame__title = "LidarView"

with SinglePageLayout(server) as layout:
    layout.toolbar = None
    layout.icon = None
    layout.title = None

    # Toolbar setup
    with layout.footer:

        # vuetify.VSpacer()  # Spacer for alignment

        # # Add checkpoint button
        # vuetify.VBtn("Add Checkpoint", click=ctrl.add_checkpoint)

        # vuetify.VSpacer()

        # vuetify.VSelect(
        #     label="Choose Checkpoint",
        #     items=("checkpoint_labels",),  # Bind to state.checkpoint_labels
        #     v_model=("selected_checkpoint", 0),  # Selected checkpoint index
        # )

        # # Navigate to the selected checkpoint
        # vuetify.VBtn(
        #     "Navigate",
        #     click=lambda: ctrl.navigate_to_checkpoint(state.selected_checkpoint)
        # )

        # vuetify.VSpacer()

        # Add Bird's-Eye View Button
        # vuetify.VBtn(
        #     "Bird's Eye View",
        #     click=ctrl.set_birds_eye_view,
        #     color="primary",
        #     outlined=True,
        # )

        # vuetify.VSpacer()

        # Add Screenshot Button
        # vuetify.VBtn(
        #     "Take Screenshot",
        #     click=ctrl.save_screenshot,
        #     color="secondary",
        #     outlined=True,
        # )

        # vuetify.VSpacer()

        # Start and Reset SLAM buttons
        # vuetify.VBtn(
        #     "Launch SLAM",
        #     click=on_slam_start,
        #     color="#5c4347",
        # )
        vuetify.VBtn(
            "Launch SLAM",
            height=60,
            width=150,
            click=on_slam_start,
            color="#5c4347",  # Button background color
            style="color: white; border: 2px solid white; font-weight: bold;"
        )
        vuetify.VBtn(
            "Reset SLAM",
            height=60,
            width=150,
            click=on_slam_start,
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )

        vuetify.VSpacer()

        
        with vuetify.VContainer(
            style="display: inline-block; width: auto; padding: 0; margin: 0; text-align: left;"
        ):
            # Add the label above the slider
            html.Html(
                "<div style='color: white; margin-bottom: 8px; font-weight: bold;'>Point Size:</div>"
            )

            # Add the Point Size Slider with custom styling
            vuetify.VSlider(
                v_model=("point_size", 3),  # Bind to state.point_size with default value 3
                min=1,
                max=7,
                step=1,
                ticks='always',
                tick_size=5,
                tick_labels=["Small", "", "", "", "", "", "Big"],  # Optional: Labels for the first and last ticks
                dense=True,
                class_="custom-slider",  # Assign the custom CSS class
                background_color="#5c4347",
                track_color="#5c4347",
                color="#f1b4be",
                style="width: 200px;",  # Adjust width as needed
            )

        vuetify.VSpacer()

        vuetify.VBtn(
            "[1] Cyan & Pink",
            height=50,
            width=130,
            click=lambda: apply_color_template("cyan_pink", view),
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )
        vuetify.VBtn(
            "[2] Red",
            height=50,
            width=130,
            click=lambda: apply_color_template("red", view),
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )
        vuetify.VBtn(
            "[3] Blue",
            height=50,
            width=130,
            click=lambda: apply_color_template("blue", view),
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )
        vuetify.VBtn(
            "[4] Yellow",
            height=50,
            width=130,
            click=lambda: apply_color_template("yellow", view),
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )
        vuetify.VBtn(
            "[5] Intensity",
            height=50,
            width=130,
            click=lambda: apply_color_template("intensity", view),
            color="#20191a",
            style="color: white; border: 2px solid white; font-weight: bold;"
        )

        vuetify.VSpacer()

        vuetify.VImg(
            src='C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/trame_app/vedette_logo.png',
            style="width: 100px; height: auto; display: block; border: 2px solid white;",
        )
        
        # html.Img(
        #     src="static/vedette_logo.png",  # URL or path to your image
        #     style="width: 100px; height: auto; border: 2px solid white;",  # Adjust size and styling
        # )

        # # Toggle Bounding Boxes button
        # vuetify.VBtn(
        #     "Toggle Bounding Boxes",
        #     click=ctrl.toggle_bounding_boxes,
        #     color="primary",
        #     outlined=True,
        # )

        # vuetify.VSpacer()

        # # Play/Pause checkbox
        # vuetify.VCheckbox(
        #     v_model=("play", True),
        #     off_icon="mdi-play",
        #     on_icon="mdi-stop",
        #     hide_details=True,
        #     dense=True,
        #     classes="mx-2",
        # )

        

        # # Reset camera button
        # with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
        #     vuetify.VIcon("mdi-crop-free")

        # # Busy progress indicator
        # vuetify.VProgressLinear(
        #     indeterminate=True,
        #     absolute=True,
        #     bottom=True,
        #     active=("trame__busy",),
        # )


        layout.footer.style = "background-color: #20191a;"

    # Content setup
    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height", style="background-color: #20191a;"):
            with vuetify.VRow(classes="fill-height", no_gutters=True):
                # Left half: LiDAR stream
                with vuetify.VCol(cols=6, classes="pa-0 fill-height", style="height: 90vh;"):
                    with vuetify.VCard(
                        style=(
                            "height: 100%; background-color: white; border-radius: 12px; "
                            "overflow: hidden; border: 2px solid white; margin: 3; padding: 3;"
                        )
                    ):
                        # Overlay Text
                        html.Div(
                            "<div style='position: absolute; top: 10px; left: 10px; color: white; font-weight: bold; z-index: 2;'>(F) LiDAR Freecam</div>",
                            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"
                        )
                        
                        # VtkRemoteLocalView
                        html_view = paraview.VtkRemoteLocalView(
                            view,  # Ensure 'view' is defined and properly configured
                            namespace="view",
                            style="height: 100%; width: 100%; position: absolute; top: 0; left: 0; z-index: 1;",
                        )
                        ctrl.view_update = html_view.update
                        ctrl.view_update_geometry = html_view.update_geometry
                        ctrl.view_update_image = html_view.update_image
                        ctrl.view_reset_camera = html_view.reset_camera

                # Right half: Map and Graph
                with vuetify.VCol(cols=6, classes="pa-0 fill-height", style="height: 90vh;"):
                    with vuetify.VRow(classes="fill-height", no_gutters=True):
                        # Top: Leaflet map
                        with vuetify.VCol(cols=12, classes="pa-0", style="height:50%; border-bottom: 1px solid #555; position: relative;"):
                            Html(
                                "<div style='position: absolute; top: 10px; left: 10px; color: black; z-index: 1; font-weight: bold;'>(P) LiDAR POV</div>"
                            )
                            with LMap(
                                height="100%",
                                zoom=15,
                                center=("drone_position", [37.7749, -122.4194]), # The map's center was bound to state.drone_position. Will update when state.drone_position updates. rn doesn't change
                                style="height:100%;"
                            ):
                                LTileLayer(
                                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                                    attribution="Map data © OpenStreetMap contributors",
                                )
                                LMarker(
                                    position=("drone_position", [37.7749, -122.4194])
                                )
                        # Bottom: Plotly graph
                        with vuetify.VCol(cols=12, classes="pa-0", style="height:50%; position: relative;"):
                            Html(
                                "<div style='position: absolute; top: 10px; left: 10px; color: black; z-index: 1; font-weight: bold;'>(C) Camera</div>"
                            )
                            plotly_graph = Figure(
                                figure=state.altitude_figure,  # Pass the Plotly figure object directly
                                style="height:100%; width:100%;",
                            )


apply_color_template("cyan_pink", view)
# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

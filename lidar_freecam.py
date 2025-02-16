import paraview.web.venv
from trame.app import get_server
from trame.widgets import paraview  # Import ParaView widgets
from trame.widgets import iframe
from paraview import simple
from lidarview import simple as lvsmp
from pathlib import Path
import asyncio
from trame.ui.html import DivLayout

import threading
# import uvicorn
# from fastapi import FastAPI
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS



# Initialize the server
server = get_server() #client_type="vue2"
state, ctrl = server.state, server.controller

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/set_color_template", methods=["POST"])
def api_set_color_template():
    print('HELLOOOOOO')
    data = request.json
    template_name = data.get("template_name")

    if template_name not in ["intensity", "cyan_pink", "red", "blue", "yellow"]:
        return jsonify({"error": "Invalid template name"}), 400

    # Send command to Trame
    apply_color_template(template_name)
    requests.post("http://127.0.0.1:1234/trame/set_color_template", json={"args": [template_name]})
    return jsonify({"status": "success", "message": f"Color template changed to {template_name}"})


def start_flask():
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

# Load LiDAR data
inputfile = 'C:/Users/alici/OneDrive/Documents/VEDETTE/vedette/test_data.pcap'
stream = lvsmp.OpenPCAP(inputfile, "VLP-16", "Velodyne")
representation = simple.Show(stream)
view = simple.GetRenderView()

# Set up the render view
view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]  # Black background
view.OrientationAxesVisibility = 0
simple.Render()


# -----------------------------------------------------------------------------
# Color Scheme
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

# Function to apply a color template
def apply_color_template(template_name, **kwargs):
    """
    Apply a color scheme to the point cloud visualization.

    Args:
        template_name (str): Name of the color template.
    """
    print(f'Applying template: {template_name}')
    
    lut = create_color_template(template_name)
    simple.ColorBy(representation, ('POINTS', 'intensity'))
    representation.LookupTable = lut

    view.Update()
    simple.Render()
    # ctrl.view_update()

# Bind function to Trame state changes
state.template_name = "cyan_pink"
state.change("color_template")(apply_color_template)

view.UseColorPaletteForBackground = 0
view.Background = [0.0, 0.0, 0.0]
view.OrientationAxesVisibility = 0
view = simple.Render()
state.slam = None

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
    size_mapping = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13}
    actual_size = size_mapping.get(point_size, 5)  # Default to 5

    representation.PointSize = actual_size
    view.Update()
    simple.Render()
    # ctrl.view_update()

# Bind function to Trame state changes
state.change("point_size")(update_point_size)

################################################################################
# Expose Trame API Endpoints

@ctrl.trigger("set_color_template")
def set_color_template(template_name):
    """Triggered by frontend to update color template."""
    
    print(f"Received trigger: colorTemplate({template_name})")  # DEBUG
    if template_name in ["intensity", "cyan_pink", "red", "blue", "yellow"]:
        apply_color_template(template_name)
        ctrl.view_update()
    else:
        print(f"Invalid color template received: {template_name}")

@ctrl.trigger("set_point_size")
def set_point_size(size):
    """Triggered by frontend to update point size."""
    print(f"Received trigger: pointSize({size})")  # DEBUG
    try:
        size = int(size)
        update_point_size(size)
        ctrl.view_update()
    except ValueError:
        print(f"Invalid point size received: {size}")

@ctrl.trigger("get_user_data")
def send_user_data():
    print("Sending user data to client...")
    # ctrl.update(user_data={"username": "asun0102"})

################################################################################


# GUI Setup
from trame.ui.vuetify import SinglePageLayout


with DivLayout(server) as layout:
    layout.toolbar = None  # Remove toolbar
    layout.icon = None  # Remove app icon
    layout.title = None  # Remove title
    layout.footer = None  # Remove footer
    comm = iframe.Communicator(target_origin="http://localhost:3000", enable_rpc=True)
    paraview.VtkRemoteLocalView(
        view,
        namespace="view",
        # style="height: 99vh; width: 99vw; max-width: 90vw; max-height: 99.5vh; margin: auto; position: relative;"
        style="height: 100vh; width: 100vw; margin: auto; position: relative;"
    )

    
    
# Start server
if __name__ == "__main__":
    # server.start()
    threading.Thread(target=start_flask, daemon=True).start()  # Start Flask in background
    server.start(port=1234)
   

# Overview
This is a web application you can run with our lightweight LiDAR drones. The application
is meant to help visualize LiDAR information being streamed from the drone to better
navigate indoor ambiguous environments.
![application](https://i.ibb.co/MyWjd3mC/Screenshot-2025-02-16-213926.png)

# Setup Instructions

### 1. Install LidarView
- Download and install LidarView from the following link:  
  [LidarView Releases](https://gitlab.kitware.com/LidarView/lidarview/-/releases)

- After installation, locate the `lvpython` executable within the LidarView application folder.

### 2. Add `lvpython` to Environment Path
- Add the path to `lvpython` as an environment variable on your system.  
  This allows you to execute `lvpython` from any command line or terminal.

### 3. Virtual Environment Setup
Whenever installing packages, first activate the virtual environment:

- **On Unix-based systems (Linux/macOS):**
  source .lvenv/Scripts/activate
  **On Windows:**
  .lvenv/Scripts/activate

After activation, use package installers to add the modules to the venv

### 4. Running applications
Run the trame_app with:

lvpython [trame application name] --venv .lvenv
  
Run frontend:
Frontend embeds the trame server in an iframe.

cd frontend/web-app
npm start

# Errors you might face
- Module not found error: make sure you package installed with the virtual environment activated
- lvpython not recognized: you did not add path to environment variables correctly
- numpy issues: go into the file that is erroring, which should be one of the installed packages in
  your venv (ex. vtkmodules\util\numpy_support.py). Manually edit all areas of numpy.int32 numpy.int64
  numpy.uint32 numpy.uint64 and change to just int
  
# Additional self notes
You can use a .pcap file as if it was a stream by running > PacketFileSender.exe test_data.pcap 
in a separate terminal to send it as a stream.
Simple.py is example code from the Kitware site on running a stream.
Currently, use lvenv2 since there are venv issues. That is the only functional one.

TO RUN: (might need to open browser in windowed mode for some reason)
- run backend on one terminal: vedette> lvpython lidar_freecam.py --venv .lvenv2
- run frontend on a separate terminal: vedette\frontend\web-app> npm start
- if you are streaming live, you are done
- if running a .pcap file, you have to stream it in a separate terminal: vedette> PacketFileSender.exe test_data.pcap

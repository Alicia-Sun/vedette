# Overview
This is a web application you can run with our lightweight LiDAR drones. The application
is meant to help visualize LiDAR information being streamed from the drone to better
navigate indoor ambiguous environments.

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
  

  

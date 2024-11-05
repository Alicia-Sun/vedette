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
  
Run other applications similarly

# Errors you might face
- Module not found error: make sure you package installed with the virtual environment activated
- lvpython not recognized: you did not add path to environment variables correctly

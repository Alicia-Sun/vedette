***Setup***

Install LidarView and pull the path for lvpython within the application folder.

Installation link: https://gitlab.kitware.com/LidarView/lidarview/-/releases

Add that path as an environment path variable for your computer so you can run lvpython.


Whenever installing packages, activate the venv:

On Unix: source .lvenv/bin/activate

On Windows: .lvenv/Scripts/activate

After activation, use package installers to add the modules to the venv


Run the trame_app with:

  lvpython <trame-python-script> --venv .lvenv
  
Run other applications similarly

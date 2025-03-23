import subprocess

# Define the commands
command1 = ["lvpython", "lidar_freecam.py", "--venv", ".lvenv2"]
command2 = ["lvpython", "lidar_pov.py", "--venv", ".lvenv2"]

# Start both processes
process1 = subprocess.Popen(command1)
process2 = subprocess.Popen(command2)

# Wait for both processes to finish
process1.wait()
process2.wait()
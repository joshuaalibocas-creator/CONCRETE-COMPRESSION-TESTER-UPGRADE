import os
import sys
import subprocess

# Secure workspace directory sync logic
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

print(f"Target Working Workspace: {os.getcwd()}")
print("Starting standalone executable compilation engine...")

# Execute PyInstaller with custom application name assignment
subprocess.run([
    sys.executable, 
    "-m", 
    "PyInstaller", 
    "--onefile", 
    "--noconsole", 
    "--name=compressionapp", 
    "app.py"
])

print("Compilation script finished complete!")

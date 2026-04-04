
import os
import subprocess
import sys

def run_cmd(cmd):
    print(f"\n# Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f"Error executing command: {e}")

print("--- Step 1: Diagnosis ---")
run_cmd("python --version")
print(f"Current Directory: {os.getcwd()}")
run_cmd("dir /s /b")

print("\n--- Running App to capture error ---")
# Use the same python as this script
run_cmd(f"{sys.executable} app/app.py")

import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    log = subprocess.check_output(['git', 'log', '--oneline', '-n', '50'], cwd=path, text=True)
    with open("git_history.txt", "w") as f:
        f.write(log)
    print("DONE log")
except Exception as e:
    print(f"Error: {e}")

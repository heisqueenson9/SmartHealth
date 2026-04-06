import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    log = subprocess.check_output(['git', 'log', '--oneline', '-n', '20'], cwd=repo_path, text=True)
    print("--- LOG START ---")
    print(log)
    print("--- LOG END ---")
except Exception as e:
    print(f"Error: {e}")

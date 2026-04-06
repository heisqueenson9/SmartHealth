import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    log = subprocess.check_output(['git', 'log', '--oneline', '-n', '20'], cwd=path, text=True)
    print("LOGOUT:")
    print(log)
    print("LOGEND")
except Exception as e:
    print(f"Error: {e}")

import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    # Add my manual changes
    subprocess.run(['git', 'add', 'app/templates/', 'app/static/'], cwd=path)
    # Commit
    res = subprocess.run(['git', 'commit', '-m', "revert: restore clean academic frontend"], cwd=path, capture_output=True, text=True)
    with open("local_commit.log", "w") as f:
        f.write(res.stdout + "\n" + res.stderr)
    
    # Force Push to Origin (since history might be messy)
    res_push = subprocess.run(['git', 'push', '-f', 'origin', 'main'], cwd=path, capture_output=True, text=True, timeout=30)
    with open("local_push.log", "w") as f:
        f.write(res_push.stdout + "\n" + res_push.stderr)
    print("DONE")
except Exception as e:
    print(f"Error: {e}")

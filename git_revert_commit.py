import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    subprocess.run(['git', 'add', '-A'], cwd=path)
    res = subprocess.run(['git', 'commit', '-m', "revert: strip cinematic animations and restore clean design system"], cwd=path, capture_output=True, text=True)
    with open("commit_revert.log", "w") as f:
        f.write(res.stdout + "\n" + res.stderr)
    print("FINISHED")
except Exception as e:
    print(f"Error: {e}")

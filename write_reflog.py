import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    log = subprocess.check_output(['git', 'reflog', '-n', '20'], cwd=repo_path, text=True)
    with open(os.path.join(repo_path, "app", "reflog.txt"), "w") as f:
        f.write(log)
    print("DONE")
except Exception as e:
    print(f"Error: {e}")

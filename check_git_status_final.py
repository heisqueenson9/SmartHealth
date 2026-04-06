import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
os.chdir(repo_path)

res = subprocess.run(['git', 'status'], capture_output=True, text=True)
with open('git_status_final.txt', 'w') as f:
    f.write(res.stdout + "\n---\n" + res.stderr)

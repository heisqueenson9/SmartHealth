import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
os.chdir(repo_path)

commands = [
    ["git", "status"],
    ["git", "branch", "-a"],
    ["git", "remote", "-v"]
]

results = []
for cmd in commands:
    res = subprocess.run(cmd, capture_output=True, text=True)
    results.append(f"COMMAND: {' '.join(cmd)}\nOUT:\n{res.stdout}\nERR:\n{res.stderr}\n")

with open('full_status.txt', 'w') as f:
    f.writelines(results)

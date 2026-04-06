import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
os.chdir(repo_path)

res = subprocess.getoutput('git diff --cached --stat')
with open('staged_stat.txt', 'w') as f:
    f.write(res)

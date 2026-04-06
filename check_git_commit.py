import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
os.chdir(repo_path)

res = subprocess.getoutput('git log -n 1 --pretty=format:%H')
with open('last_commit.txt', 'w') as f:
    f.write(res)

import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
print(f"CWD: {os.getcwd()}")
try:
    log = subprocess.check_output(['git', 'log', '--oneline', '-n', '20'], cwd=path, text=True)
    with open(os.path.join(path, "commits.txt"), "w") as f:
        f.write(log)
    print("DONE: wrote to " + os.path.join(path, "commits.txt"))
except Exception as e:
    print(f"ERROR: {e}")

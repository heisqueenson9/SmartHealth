import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    # List files modified since 578a1b4 in templates and static
    diff = subprocess.check_output(['git', 'diff', '--name-only', '578a1b4', 'HEAD', '--', 'app/templates/', 'app/static/'], cwd=path, text=True)
    with open("diff_files.txt", "w") as f:
        f.write(diff)
    print("DONE diff")
except Exception as e:
    print(f"Error: {e}")

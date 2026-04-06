import subprocess
repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    diff = subprocess.check_output(['git', 'diff', '08ff434', 'HEAD', '--name-only', '--', 'app/templates/', 'app/static/'], cwd=repo_path, text=True)
    with open("diff_files.txt", "w") as f:
        f.write(diff)
    print("DONE")
except Exception as e:
    print(f"ERROR: {e}")

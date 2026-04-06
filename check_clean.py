import subprocess
repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    content = subprocess.check_output(['git', 'show', '08ff434:app/templates/index.html'], cwd=repo_path, text=True)
    with open("index_clean.html", "w") as f:
        f.write(content)
    print("DONE")
except Exception as e:
    print(f"ERROR: {e}")

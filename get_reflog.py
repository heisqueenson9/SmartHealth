import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
output_file = os.path.join(repo_path, "actual_git_reflog.txt")

try:
    result = subprocess.run(
        ["git", "reflog", "-n", "100"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    print(f"Reflog written to {output_file}")
except Exception as e:
    print(f"Error: {e}")

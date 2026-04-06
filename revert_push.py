import subprocess
import os

os.chdir(r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI")

try:
    print("ADDING...")
    subprocess.run(['git', 'add', '-A'], check=True)
    print("COMMITTING...")
    subprocess.run(['git', 'commit', '-m', "revert: fix mobile nav visibility and analysis box overflow on mobile"], check=True)
    print("PUSHING...")
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("SUCCESS.")
except Exception as e:
    print(f"FAILED: {str(e)}")

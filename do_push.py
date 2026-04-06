import subprocess
import os

os.chdir(r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI")

with open('push_out.txt', 'w') as f:
    try:
        out = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
        f.write(f"ADD OUT:\n{out.stdout}\n{out.stderr}\n\n")

        out = subprocess.run(['git', 'commit', '-m', "fix: mobile nav visibility and analysis box overflow on mobile"], capture_output=True, text=True)
        f.write(f"COMMIT OUT:\n{out.stdout}\n{out.stderr}\n\n")

        out = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        f.write(f"PUSH OUT:\n{out.stdout}\n{out.stderr}\n\n")
    except Exception as e:
        f.write(f"ERROR: {str(e)}\n")

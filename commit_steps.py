import subprocess
import os

os.chdir(r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI")

with open('commit_steps.txt', 'w') as f:
    # Step 1
    out = subprocess.run(['git', 'status'], capture_output=True, text=True)
    f.write(f"STEP 1:\n{out.stdout}\n\n")

    # Step 2
    out = subprocess.run(['git', 'checkout', 'main'], capture_output=True, text=True)
    f.write(f"STEP 2:\n{out.stdout}\n{out.stderr}\n\n")

    # Step 3
    out = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
    
    # Step 4
    out = subprocess.run(['git', 'status'], capture_output=True, text=True)
    f.write(f"STEP 4:\n{out.stdout}\n\n")

    # Step 5
    out = subprocess.run(['git', 'commit', '-m', "fix: full responsive layout, animation restoration, mobile/desktop fixes across all pages"], capture_output=True, text=True)
    f.write(f"STEP 5:\n{out.stdout}\n{out.stderr}\n\n")

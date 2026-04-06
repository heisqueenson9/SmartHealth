import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    # Try to find the last commit BEFORE the animation prompt.
    # The animation prompt was Conversation 3582494d...
    # I'll check the log for messages.
    log = subprocess.check_output(['git', 'log', '--oneline', '-n', '30'], cwd=path, text=True)
    with open("git_log_v3.txt", "w") as f:
        f.write(log)
    print("DONE log")
    
    # Check if a commit matches "fix: mobile navigation menu overlay"
    # This was REQ 2 in the summary, before the cinematic prompt (likely).
    target_hash = None
    for line in log.splitlines():
        if "fix: mobile nav" in line.lower():
            target_hash = line.split()[0]
            break
    
    if target_hash:
        print(f"FOUND target hash: {target_hash}")
        # Reset to that hash
        res = subprocess.run(['git', 'reset', '--hard', target_hash], cwd=path, capture_output=True, text=True)
        with open("reset_res.txt", "w") as f:
            f.write(res.stdout + "\n" + res.stderr)
        print("RESET DONE")
    else:
        print("TARGET COMMIT NOT FOUND")

except Exception as e:
    print(f"ERROR: {e}")

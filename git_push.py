import subprocess
import os

with open('push_log.txt', 'w') as f:
    cmd = ['git', 'push', '-u', 'origin', 'main']
    try:
        f.write("Starting push...\n")
        # Run explicitly with a 30 second timeout just in case it hangs on credentials
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        f.write(f"STDOUT:\n{result.stdout}\n")
        f.write(f"STDERR:\n{result.stderr}\n")
        f.write(f"RETURN CODE: {result.returncode}\n")
    except Exception as e:
        f.write(f"FAILED: {str(e)}\n")

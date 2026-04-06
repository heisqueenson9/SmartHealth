import subprocess
import os

env = os.environ.copy()
env['GIT_TERMINAL_PROMPT'] = '0'
env['GCM_INTERACTIVE'] = 'never'

try:
    result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], capture_output=True, text=True, timeout=15, env=env)
    with open('push_out.txt', 'w') as f:
        f.write(result.stdout + "\n---\n" + result.stderr)
except Exception as e:
    with open('push_out.txt', 'w') as f:
        f.write("Exception: " + str(e))

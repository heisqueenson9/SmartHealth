import subprocess
with open('actual_git_log.txt', 'w') as f:
    subprocess.run(['git', 'log', '--oneline'], stdout=f, stderr=subprocess.STDOUT)

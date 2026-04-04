import subprocess

def run_git():
    commands = [
        ['git', 'remote', 'add', 'origin', 'https://github.com/heisqueenson9/SmartHealth.git'],
        ['git', 'add', '.'],
        ['git', 'commit', '-m', 'feat: implement Vercel serverless Flask integration'],
        ['git', 'push', '-u', 'origin', 'main']
    ]
    with open('git_log.txt', 'w') as f:
        for cmd in commands:
            f.write(f"Executing: {' '.join(cmd)}\n")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
                f.write(f"RETURN CODE: {result.returncode}\n\n")
            except Exception as e:
                f.write(f"EXCEPTION: {str(e)}\n\n")

if __name__ == '__main__':
    run_git()

import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
clean_commit = "08ff434387323c720e0e2a64aa42c2503d19d5b8"
log_file = "rollback_log.txt"

def run_git(args):
    try:
        res = subprocess.check_output(['git'] + args, cwd=repo_path, text=True, stderr=subprocess.STDOUT)
        return res
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output}"

with open(log_file, "w") as log:
    log.write("=== Git Log ===\n")
    log.write(run_git(['log', '--oneline', '-n', '20']))
    log.write("\n\n=== Changed Files ===\n")
    diff = run_git(['diff', clean_commit, 'HEAD', '--name-only', '--', 'app/templates/', 'app/static/'])
    log.write(diff)
    
    files = [f.strip() for f in diff.split('\n') if f.strip()]
    log.write(f"\n\n=== Restoring {len(files)} files ===\n")
    for file in files:
        run_git(['checkout', clean_commit, '--', file])
        log.write(f"Restored {file}\n")
    
    log.write("\n\n=== Git Status After Restore ===\n")
    log.write(run_git(['status']))
    
    run_git(['add', 'app/templates/', 'app/static/'])
    log.write("\n\n=== Final Commit ===\n")
    log.write(run_git(['commit', '-m', "revert: restore frontend to last clean working state (commit 08ff434)"]))

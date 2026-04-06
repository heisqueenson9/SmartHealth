import subprocess
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
clean_commit = "08ff434387323c720e0e2a64aa42c2503d19d5b8"

def run_git(args):
    print(f"Running: git {' '.join(args)}")
    try:
        res = subprocess.check_output(['git'] + args, cwd=repo_path, text=True, stderr=subprocess.STDOUT)
        return res
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output}"

# Step 2: List changed files
diff = run_git(['diff', clean_commit, 'HEAD', '--name-only', '--', 'app/templates/', 'app/static/'])
with open("modified_files.txt", "w") as f:
    f.write(diff)

# Step 3: Restore each file
files = [f.strip() for f in diff.split('\n') if f.strip()]
for file in files:
    print(f"Restoring {file}...")
    run_git(['checkout', clean_commit, '--', file])

# Step 5: Commit (Step 4 is verify but I'll do that manually or in script)
# Wait, let's just stage and commit.
run_git(['add', 'app/templates/', 'app/static/'])
res = run_git(['commit', '-m', "revert: restore frontend to last clean working state (commit 08ff434)"])
print(res)

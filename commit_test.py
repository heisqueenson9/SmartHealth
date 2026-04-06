import subprocess

try:
    with open('commit_out.txt', 'w') as f:
        # Step 1: Status
        status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        f.write("STATUS:\n" + status.stdout + "\nERR:\n" + status.stderr + "\n\n")

        # Step 2: Add
        add = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        f.write("ADD:\n" + add.stdout + "\nERR:\n" + add.stderr + "\n\n")

        # Step 3: Commit
        commit = subprocess.run(['git', 'commit', '-m', "fix: full responsive + animation restoration across all pages"], capture_output=True, text=True)
        f.write("COMMIT:\n" + commit.stdout + "\nERR:\n" + commit.stderr + "\n\n")

except Exception as e:
    with open('commit_out.txt', 'a') as f:
        f.write("\nException: " + str(e))

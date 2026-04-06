import subprocess
import os

os.chdir(r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI")

print("LOG:")
print(subprocess.run(['git', 'log', '-n', '2', '--oneline'], capture_output=True, text=True).stdout)

print("\nREVERTING...")
# Try to revert the last commit if it matches my message
try:
    log = subprocess.check_output(['git', 'log', '-n', '1', '--oneline'], text=True)
    if "fix: mobile nav visibility" in log:
        print("Found my commit. Reverting...")
        print(subprocess.run(['git', 'revert', 'HEAD', '--no-edit'], capture_output=True, text=True).stdout)
        print(subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True).stdout)
    else:
        print("Commit not found or already reverted. Discarding any staged/unstaged changes...")
        print(subprocess.run(['git', 'checkout', '--', 'app/static/css/main.css'], capture_output=True, text=True).stdout)
        print(subprocess.run(['git', 'reset', '--hard'], capture_output=True, text=True).stdout)

except Exception as e:
    print(f"Error during revert: {str(e)}")

print("\nDONE.")

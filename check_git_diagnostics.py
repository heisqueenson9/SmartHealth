import subprocess
import os

os.chdir(r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI")

try:
    print("STATUS:")
    print(subprocess.check_output(['git', 'status'], text=True))
    print("\nLOG:")
    print(subprocess.check_output(['git', 'log', '-n', '1', '--oneline'], text=True))
    print("\nREMOTE:")
    print(subprocess.check_output(['git', 'remote', '-v'], text=True))
except Exception as e:
    print(f"ERROR: {str(e)}")

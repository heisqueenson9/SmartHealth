import subprocess
import os

path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
try:
    tree = subprocess.check_output(['git', 'ls-tree', '-r', '578a1b4', '--name-only'], cwd=path, text=True)
    with open("tree_578a1b4.txt", "w") as f:
        f.write(tree)
    print("DONE tree")
except Exception as e:
    print(f"Error: {e}")

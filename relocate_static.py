import shutil
import os

repo_path = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI"
src = os.path.join(repo_path, 'app', 'static')
dst = os.path.join(repo_path, 'static')

if not os.path.exists(dst):
    os.makedirs(dst)

# Copy everything
for item in os.listdir(src):
    s = os.path.join(src, item)
    d = os.path.join(dst, item)
    if os.path.isdir(s):
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        shutil.copy2(s, d)

# Verify
if os.path.exists(os.path.join(dst, 'css', 'main.css')):
    print("SUCCESS: Static files moved to root/static")
else:
    print("FAILURE: Copy failed")

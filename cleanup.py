import os
import shutil

files_to_delete = [
    'test_env.bat', 'test_output.py', 'pyvenv.cfg', '.renderignore', 
    'audit_step1.py', 'audit_temp.py', 'run_diagnosis.py', 'test_app_init.py', 
    'test_import_app.py', 'test_imports.py', 'test_routes.py', 'viva_test.py'
]

dirs_to_delete = ['notebooks', 'report', 'venv']

base_path = r'c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI'

for f in files_to_delete:
    pth = os.path.join(base_path, f)
    if os.path.exists(pth):
        try:
            os.remove(pth)
            print(f"Deleted file: {f}")
        except Exception as e:
            print(f"Error deleting file {f}: {e}")

for d in dirs_to_delete:
    pth = os.path.join(base_path, d)
    if os.path.exists(pth):
        try:
            shutil.rmtree(pth)
            print(f"Deleted dir: {d}")
        except Exception as e:
            print(f"Error deleting dir {d}: {e}")

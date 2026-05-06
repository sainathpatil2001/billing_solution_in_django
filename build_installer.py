
import os
import subprocess
import shutil
import sys

def run_command(cmd, cwd=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)

def main():
    print("=== Building Billing System Installer ===")
    
    # Ensure in correct dir
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Clean previous builds
    print("Cleaning...")
    if os.path.exists("dist"):
        try: shutil.rmtree("dist")
        except: pass
    if os.path.exists("dist-python"):
        try: shutil.rmtree("dist-python")
        except: pass
    if os.path.exists("build"):
        try: shutil.rmtree("build")
        except: pass

    # Prepare initial DB
    if os.path.exists("db.sqlite3"):
        shutil.copy("db.sqlite3", "initial_db.sqlite3")
    else:
        print("Warning: db.sqlite3 not found. Bundled app will start empty.")
        # Create empty file to avoid error in add-data?
        # open("initial_db.sqlite3", 'a').close()
        pass

    # 1. Build Django Backend
    print("\n--- Building Django Backend ---")
    
    # Collect template/static data args
    # Note: Separator is ; for Windows
    add_data = [
        "genrate_bill/templates;genrate_bill/templates",
        "inventory/templates;inventory/templates",
        "static;static",
        "media;media",
        "initial_db.sqlite3;."
    ]
    
    add_data_str = " ".join([f'--add-data "{x}"' for x in add_data])
    
    hidden_imports = [
        "genrate_bill.apps",
        "inventory.apps",
        "genrate_bill.urls",
        "inventory.urls",
        "bill_maker.urls",
        "django.contrib.admin.apps",
        "django.contrib.auth.apps",
        "django.contrib.contenttypes.apps",
        "django.contrib.messages.apps",
        "django.contrib.sessions.apps",
        "django.contrib.staticfiles.apps",
    ]
    
    hidden_imports_str = " ".join([f'--hidden-import "{x}"' for x in hidden_imports])
    
    cmd = (
        f'python -m PyInstaller --noconfirm --onedir --console --clean --name "django_app" '
        f'--distpath "dist-python" '
        f'{add_data_str} '
        f'{hidden_imports_str} '
        'run_django.py'
    )
    
    run_command(cmd)

    # 2. Build Electron Frontend & Installer
    print("\n--- Building Desktop Installer ---")
    
    # Check if node_modules exists
    if not os.path.exists("node_modules"):
        run_command("npm install")
    
    run_command("npm run build-win")

    print("\n=== Build Complete ===")
    print("Installer located in: dist/")
    
    # Cleanup temp db copy
    if os.path.exists("initial_db.sqlite3"):
        os.remove("initial_db.sqlite3")

if __name__ == "__main__":
    main()

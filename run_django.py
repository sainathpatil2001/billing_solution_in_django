
import os
import sys
import shutil
import traceback
import time
from pathlib import Path

# Force unbuffered output immediately
sys.stdout.reconfigure(encoding='utf-8')

print("Backend process starting...", flush=True)

import django
from django.core.management import call_command

def main():
    print("Entering main functionality...", flush=True)
    
    # Setup environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill_maker.settings')
    
    # Ensure project root is in path
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    sys.path.insert(0, base_dir)
    print(f"Base dir: {base_dir}", flush=True)
    
    # Initialize Django
    print("Setting up Django...", flush=True)
    try:
        django.setup()
        print("Django setup complete.", flush=True)
    except Exception as e:
        print(f"Failed to setup Django: {e}", flush=True)
        traceback.print_exc()
        return

    # Handle Database Initialization for Frozen App
    if getattr(sys, 'frozen', False):
        print("Checking database...", flush=True)
        app_data = os.getenv('APPDATA')
        if app_data:
            APP_DATA_DIR = Path(app_data) / "BillingSystem"
            APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            db_path = APP_DATA_DIR / 'db.sqlite3'
            
            if not db_path.exists():
                print("First run detected.", flush=True)
                
                # Check for bundled initial DB
                bundled_db = Path(sys._MEIPASS) / 'initial_db.sqlite3'
                if bundled_db.exists():
                     print(f"Copying initial database from {bundled_db}...", flush=True)
                     shutil.copy(bundled_db, db_path)
            
            # Always run migrations to ensure schema is consistent
            print("Running database migrations...", flush=True)
            try:
                call_command('migrate', interactive=False)
                print("Database migrations completed.", flush=True)
            except Exception as e:
                print(f"Error running migrations: {e}", flush=True)
                traceback.print_exc()

            # Handle Media Files (Logos, Signatures, etc.)
            media_path = APP_DATA_DIR / 'media'
            if not media_path.exists():
                 print("Initializing media directory...", flush=True)
                 bundled_media = Path(sys._MEIPASS) / 'media'
                 if bundled_media.exists():
                     print(f"Copying default media from {bundled_media}...", flush=True)
                     try:
                        shutil.copytree(bundled_media, media_path)
                        print("Media files copied.", flush=True)
                     except Exception as e:
                        print(f"Error copying media files: {e}", flush=True)
                        traceback.print_exc()
                 else:
                     print("No bundled media found, creating empty media dir.", flush=True)
                     media_path.mkdir(parents=True, exist_ok=True)

    # Import WSGI App
    print("Importing WSGI app...", flush=True)
    try:
        from bill_maker.wsgi import application
    except ImportError as e:
        print(f"Failed to import WSGI application: {e}", flush=True)
        traceback.print_exc()
        return

    # Import Waitress securely
    print("Importing Waitress...", flush=True)
    try:
        from waitress import serve
    except ImportError as e:
        print(f"Failed to import Waitress: {e}", flush=True)
        print("Waitress not found. Please ensure it is installed and built correctly.", flush=True)
        traceback.print_exc()
        return

    print("Starting Waitress Server on port 8000...", flush=True)
    # Signal readiness to Electron
    print("Starting development server at http://127.0.0.1:8000/", flush=True) 
    
    try:
        serve(application, host='127.0.0.1', port=8000, threads=4)
    except Exception as e:
        print(f"Server error: {e}", flush=True) 
        traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Critical error in execution: {e}", flush=True)
        traceback.print_exc()

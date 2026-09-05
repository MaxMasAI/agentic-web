import os
import subprocess
import sys
import shutil

def create_executable():
    print("========================================")
    print(" Building Standalone Agentic Web Console")
    print("========================================")
    
    # 1. Ensure PyInstaller is installed
    try:
        import PyInstaller
        print("[OK] PyInstaller is already installed.")
    except ImportError:
        print("[!] PyInstaller not found. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed successfully.")

    # 2. Clean previous build artifacts if they exist
    print("\n[*] Cleaning previous build artifacts...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"  -> Removed {folder}/")

    # 3. Define the PyInstaller command
    sep = os.pathsep
    build_command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",          # Create a one-folder bundle containing an executable
        "--windowed",        # Do not provide a console window for standard i/o (GUI app)
        "--name", "agentic-web",
        "--contents-directory", ".",
        # Exclude conflicting Qt bindings that trigger PyInstaller hook conflicts
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        # Explicit hidden imports to prevent missing runtime modules
        "--hidden-import", "pydantic",
        "--hidden-import", "dotenv",
        "--hidden-import", "sqlite3",
        "--hidden-import", "requests",
        "--hidden-import", "aiohttp",
        "--hidden-import", "websockets",
        "--hidden-import", "uvicorn",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
    ]
    
    # Dynamically include ALL project folders in the root directory
    # (Excluding git, python virtualenvs/caches, build folders, and logs)
    exclude_dirs = {
        ".git", "__pycache__", "build", "dist", "logs", "tests",
        "venv", ".venv", "env", ".agents", ".idea", ".vscode"
    }
    for item in os.listdir("."):
        if os.path.isdir(item) and item not in exclude_dirs:
            # This ensures EVERY folder (gui, services, json, plugins, voice, bin, etc.) is included
            build_command.extend(["--add-data", f"{item}{sep}{item}"])
    
    # Include important data files sitting in the root folder
    root_data_files = [".env", "db.sqlite", "windows.xml", "linux.xml", "mac.xml"]
    for file_name in root_data_files:
        if os.path.exists(file_name):
            build_command.extend(["--add-data", f"{file_name}{sep}."])
            
    # The main entry point script
    build_command.append("app.py")
    
    print(f"\n[*] Running PyInstaller command:\n  {' '.join(build_command)}\n")
    
    # 4. Execute the build
    result = subprocess.run(build_command)
    
    if result.returncode == 0:
        dist_app_dir = os.path.join("dist", "agentic-web")
        print("\n[*] Synchronizing workspace files into distribution folder...")
        
        # Ensure all data directories and config files exist directly in dist
        for folder_name in ["json", "tasks", "logs", "downloads", "visuals", "tests", "plugins"]:
            if os.path.exists(folder_name):
                dest_dir = os.path.join(dist_app_dir, folder_name)
                shutil.copytree(folder_name, dest_dir, dirs_exist_ok=True)
                
        for file_name in root_data_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, os.path.join(dist_app_dir, file_name))
                
        print("=======================================================")
        print("✅ SUCCESS: Build completed successfully!")
        print("You can find the standalone application in the 'dist/agentic-web' folder.")
        print("Simply double click 'dist/agentic-web/agentic-web.exe' to run.")
        print("=======================================================\n")
    else:
        print("\n❌ ERROR: Build failed. Please check the error output above.")

if __name__ == "__main__":
    create_executable()

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
        "--onefile",         # Create a single portable standalone executable
        "--windowed",        # Do not provide a console window for standard i/o (GUI app)
        "--name", "agentic-web",
        # Exclude conflicting Qt bindings that trigger PyInstaller hook conflicts
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        # Collect all assets and drivers for critical packages
        "--collect-all", "playwright",
        "--collect-all", "google.genai",
        "--collect-all", "uvicorn",
        "--collect-all", "fastapi",
        "--collect-all", "sounddevice",
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
        "--hidden-import", "core.main",
        "--hidden-import", "core.agents",
        "--hidden-import", "core.agentlist",
        "--hidden-import", "core.squad_learner",
        "--hidden-import", "core.agent_status",
        "--hidden-import", "browser.browser_helpers",
        "--hidden-import", "browser.browser_controller",
        "--hidden-import", "browser.downloader",
        "--hidden-import", "utils.launcher",
        "--hidden-import", "utils.chat_session_manager",
        "--hidden-import", "utils.latency_manager",
        "--hidden-import", "utils.pid_tracker",
        "--hidden-import", "utils.enhanced_memory",
        "--hidden-import", "voice.voice_narrator",
        "--hidden-import", "voice.backend.server",
        "--hidden-import", "voice.backend.tools",
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
        exe_path = os.path.join("dist", "agentic-web.exe")
        print("=======================================================")
        print("✅ SUCCESS: Build completed successfully!")
        print("Your single standalone executable is ready at:")
        print(f"  👉 {exe_path}")
        print("\nAll runtime files (tasks, logs, downloads, visuals, json) will be")
        print("cleanly stored in %APPDATA%\\AgenticWeb without polluting your folders.")
        print("=======================================================\n")
    else:
        print("\n❌ ERROR: Build failed. Please check the error output above.")


if __name__ == "__main__":
    create_executable()

"""
scratch/test_task_launch.py - Diagnostic test for task dispatching and pipeline execution.
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_imports():
    print("[*] Testing core module imports...")
    try:
        from core import agentlist
        print("[+] agentlist imported successfully")
        from services.system_app_launcher import is_system_app_task, execute_system_app_launch
        print("[+] system_app_launcher imported successfully")
        from browser.browser_controller import is_direct_browser_or_media_task
        print("[+] browser_controller imported successfully")
        from core.main import run_agent_loop
        print("[+] core.main imported successfully")
        from utils.launcher import main as launcher_main
        print("[+] utils.launcher imported successfully")
        from gui.pages.task_dispatch import TaskDispatchPage
        print("[+] TaskDispatchPage imported successfully")
        from gui.widgets.pool_monitor import PoolMonitor
        print("[+] PoolMonitor imported successfully")
        from gui.widgets.workflow_hud_widget import WorkflowHUDWidget
        print("[+] WorkflowHUDWidget imported successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    success = test_imports()
    print(f"\nImport test result: {'PASSED' if success else 'FAILED'}")

"""
launcher.py - Root CLI entry point for launching pipeline tasks.
"""

import sys
import os

if __name__ == "__main__":
    # Ensure workspace root is in sys.path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    from utils.launcher import main
    main()

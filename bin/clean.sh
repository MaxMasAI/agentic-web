#!/usr/bin/env bash
# ==============================================================================
# Workspace Cleanup Script - Removes build artifacts, caches, and temporary logs
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

echo "[*] Cleaning build and distribution directories..."
rm -rf build dist *.spec *.egg-info .pytest_cache .coverage

echo "[*] Purging Python __pycache__ directories and .pyc files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "[*] Cleaning temporary test outputs and scratch files..."
rm -rf logs/live_*.log logs/*.tmp

echo "[OK] Cleanup complete. Workspace is clean."

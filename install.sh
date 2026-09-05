#!/usr/bin/env bash
# ==============================================================================
# Agentic Web Workstation - Linux / macOS Automated Installer
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "============================================================"
echo "  AGENTIC WORKSTATION & MULTI-AGENT AI PLATFORM INSTALLER"
echo "============================================================"
echo -e "${NC}"

# 1. Verify Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed or not in PATH!${NC}"
    echo "Please install Python 3.10+ (e.g., sudo apt install python3 python3-venv python3-pip)"
    exit 1
fi

echo -e "${GREEN}[*] Python detected:${NC} $(python3 --version)"
echo ""

# 2. Initialize Workspace Directories
echo -e "${CYAN}[*] Initializing workspace directories...${NC}"
mkdir -p logs tasks downloads visuals json tests logs/chats browser
echo -e "${GREEN}[OK] Workspace directories ready.${NC}"
echo ""

# 3. Create and Activate Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "${CYAN}[*] Creating virtual environment (venv)...${NC}"
    python3 -m venv venv || {
        echo -e "${YELLOW}[!] python3-venv might not be installed. Attempting with virtualenv...${NC}"
        virtualenv venv 2>/dev/null || true
    }
fi

if [ -f "venv/bin/activate" ]; then
    echo -e "${CYAN}[*] Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# 4. Upgrade pip
echo -e "${CYAN}[*] Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel --quiet

# 5. Install Python Dependencies
echo -e "${CYAN}[*] Installing dependencies from requirements.txt...${NC}"
echo "    (This may take 1-2 minutes depending on your internet connection)"
pip install -r requirements.txt || {
    echo -e "${YELLOW}[!] Installing core packages with fallback...${NC}"
    pip install PySide6 pydantic requests aiohttp fastapi uvicorn websockets python-dotenv mcp playwright pillow google-genai
}

# 6. Install Playwright Browser Drivers
echo ""
echo -e "${CYAN}[*] Installing Playwright Chromium browser binary for autonomous agents...${NC}"
playwright install chromium || echo -e "${YELLOW}[!] Playwright browser install skipped (can be run later via 'playwright install')${NC}"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  INSTALLATION COMPLETE! ALL DEPENDENCIES READY.${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  ${CYAN}[+] To launch the application on Linux/macOS:${NC}"
echo "      source venv/bin/activate"
echo "      python3 app.py"
echo ""

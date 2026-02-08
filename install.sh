#!/bin/bash

# Network Automator - Installation Script
# Simple and safe installation for Unix-like systems

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project information
PROJECT_NAME="Network Automator"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 ${PROJECT_NAME} - Installation Script${NC}"
echo "================================================="

# Check if Python is available
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed or not in PATH${NC}"
    echo -e "${YELLOW}Please install Python 3.8+ and try again${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓ Found Python ${PYTHON_VERSION}${NC}"

# Verify minimum Python version (3.8+)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ Python version is compatible${NC}"
else
    echo -e "${RED}❌ Error: Python 3.8+ is required (found ${PYTHON_VERSION})${NC}"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ Error: pip3 is not installed${NC}"
    echo -e "${YELLOW}Please install pip3 and try again${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip3 is available${NC}"

# Check if we're in the project directory
if [ ! -f "${PROJECT_DIR}/pyproject.toml" ]; then
    echo -e "${RED}❌ Error: pyproject.toml not found${NC}"
    echo -e "${YELLOW}Please run this script from the network-automator directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project files found${NC}"

# Create virtual environment if it doesn't exist
VENV_DIR="${PROJECT_DIR}/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "${VENV_DIR}/bin/activate"

# Upgrade pip in virtual environment
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1

# Install the project
echo -e "${YELLOW}Installing Network Automator...${NC}"
pip install -e . > /dev/null 2>&1

echo -e "${GREEN}✓ Installation completed successfully!${NC}"

# Test installation
echo -e "${YELLOW}Testing installation...${NC}"
if command -v nacli &> /dev/null; then
    echo -e "${GREEN}✓ nacli command is available${NC}"

    # Show version
    echo ""
    nacli version
    echo ""
else
    echo -e "${RED}❌ Warning: nacli command not found in PATH${NC}"
    echo -e "${YELLOW}You can still use: source .venv/bin/activate && nacli${NC}"
fi

# Installation summary
echo -e "${GREEN}"
echo "╭────────────────────────────────────────────────────────────────╮"
echo "│                    Installation Complete!                     │"
echo "╰────────────────────────────────────────────────────────────────╯"
echo -e "${NC}"

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "1. Activate the virtual environment:"
echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo -e "2. Configure your devices in:"
echo -e "   ${YELLOW}inventory/devices.yml${NC}"
echo ""
echo -e "3. Start using the CLI:"
echo -e "   ${YELLOW}nacli --help${NC}"
echo -e "   ${YELLOW}nacli examples${NC}"
echo -e "   ${YELLOW}nacli list${NC}"
echo ""
echo -e "4. Or use the project wrapper:"
echo -e "   ${YELLOW}./nacli --help${NC}"
echo ""
echo -e "${BLUE}Note:${NC} Installation is contained in the project directory."
echo -e "To uninstall, simply delete this folder."

echo ""
echo -e "${GREEN}Happy network automation! 🎉${NC}"

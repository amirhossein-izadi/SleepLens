#!/usr/bin/env bash
# ==============================================================================
# SleepLens Automated Setup Script
# Configures backend virtual environment, database migrations, metric catalog,
# and frontend npm packages in a single command.
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

GREEN="\033[92m"
BLUE="\033[94m"
YELLOW="\033[93m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n${BOLD}${BLUE}========================================================"
echo -e " 🚀 Setting Up SleepLens Decision Support System"
echo -e "========================================================${RESET}\n"

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Error: python3 is not installed or not in PATH.${RESET}"
    exit 1
fi
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e " ${GREEN}✓${RESET} Detected Python ${PYTHON_VER}"

# 2. Check Node & NPM
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Error: node is not installed. Please install Node.js 18+ (https://nodejs.org).${RESET}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}Error: npm is not installed.${RESET}"
    exit 1
fi
NODE_VER=$(node -v)
echo -e " ${GREEN}✓${RESET} Detected Node.js ${NODE_VER} and npm $(npm -v)"

# 3. Setup Python Virtual Environment in .venv
echo -e "\n${BOLD}[1/4] Setting up Python Virtual Environment...${RESET}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e " ${GREEN}✓${RESET} Created virtual environment at .venv"
else
    echo -e " ${GREEN}✓${RESET} Existing virtual environment found at .venv"
fi

# Upgrade pip and install backend requirements
.venv/bin/pip install --upgrade pip --quiet
echo -e " Installing backend dependencies from requirements.txt..."
.venv/bin/pip install -r requirements.txt --quiet
echo -e " ${GREEN}✓${RESET} Backend Python packages installed."

# 4. Run Database Migrations
echo -e "\n${BOLD}[2/4] Initializing Database & Running Migrations...${RESET}"
.venv/bin/python manage.py migrate --no-input
echo -e " ${GREEN}✓${RESET} Database schema up-to-date."

# 5. Seed Metric Catalog
echo -e "\n${BOLD}[3/4] Seeding Clinical Metric Definitions Catalog...${RESET}"
.venv/bin/python manage.py seed_metrics
echo -e " ${GREEN}✓${RESET} 20 clinical metrics and normal reference ranges seeded."

# 6. Install Frontend Node Packages
echo -e "\n${BOLD}[4/4] Installing Frontend Node Packages...${RESET}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e " ${GREEN}✓${RESET} node_modules already present; validating packages..."
    npm install --quiet
fi
cd "$DIR"
echo -e " ${GREEN}✓${RESET} Frontend packages installed successfully."

# 7. Summary & Next Steps
echo -e "\n${BOLD}${GREEN}========================================================"
echo -e " 🎉 SleepLens Setup Complete!"
echo -e "========================================================${RESET}"
echo -e "To start the system:"
echo -e "  ${BOLD}./run_all.sh${RESET}"
echo -e ""
echo -e "Services will be accessible at:"
echo -e "  • Web Workstation: ${BLUE}http://127.0.0.1:3000${RESET}"
echo -e "  • Django API:      ${BLUE}http://127.0.0.1:8000${RESET}"
echo -e "  • Admin Panel:     ${BLUE}http://127.0.0.1:8000/admin/${RESET} (admin / admin123)"
echo -e ""
echo -e "To ingest the 197 Sleep-EDF real recordings:"
echo -e "  ${BOLD}.venv/bin/python manage.py ingest_sleep_edf${RESET}\n"

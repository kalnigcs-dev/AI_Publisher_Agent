#!/usr/bin/env bash
# AI Publisher - Ubuntu VM Automated Environment Setup
# Milestone 7: VM Deployment script

set -euo pipefail

echo "=== [1/5] Verifying system dependencies ==="
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-venv python3-pip git curl sqlite3
else
    echo "Warning: apt-get not found. Assuming required packages are installed."
fi

echo "=== [2/5] Checking Antigravity CLI (agy) ==="
if ! command -v agy >/dev/null 2>&1; then
    echo "Antigravity CLI ('agy') not found in PATH."
    echo "Please ensure agy is installed and authenticated."
    echo "Visit: https://antigravity.google or follow your team installation guide."
    exit 1
fi
echo "Found agy: $(command -v agy) (version $(agy --version 2>/dev/null || echo 'unknown'))"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== [3/5] Setting up Python virtual environment ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"

mkdir -p data

echo "=== [4/5] Configuring environment & database ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example. Please review and update credentials."
fi

# Initialize database schema
.venv/bin/python -c "from publisher_mcp.database import db; db.init_db(); print('Database initialized at:', db.get_db_path())"

echo "=== [5/5] Registering local MCP server with agy ==="
PYTHON_EXEC="$PROJECT_ROOT/.venv/bin/python"
agy mcp add publisher -- "$PYTHON_EXEC" -m publisher_mcp.server || true

echo "=== Setup complete! ==="
echo "You can test the system status by running:"
echo "  agy -p 'call get_system_status on publisher' --dangerously-skip-permissions"

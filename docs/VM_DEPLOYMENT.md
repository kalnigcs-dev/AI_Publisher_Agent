# AI Publisher - VM Deployment & Scheduling Guide

This guide covers deploying the AI Publisher system to an Ubuntu Cloud VM (Milestones 7 & 8) and scheduling it via systemd user services.

---

## 1. Prerequisites on Ubuntu VM

- Ubuntu 22.04 LTS or 24.04 LTS
- Python 3.11+ (Python 3.12/3.13)
- Git and curl
- Antigravity CLI (`agy`) installed and authenticated

---

## 2. Setup Steps

```bash
# 1. Clone repository to user home directory
cd ~
git clone <repo-url> ai-publisher
cd ai-publisher

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env with your WordPress credentials and settings:
nano .env

# 4. Initialize SQLite Database
python -c "from publisher_mcp.database import db; db.init_db()"

# 5. Register Publisher MCP server with agy
agy mcp add publisher -- "$PWD/.venv/bin/python" -m publisher_mcp.server

# 6. Verify connectivity
agy -p "call get_system_status on publisher" --dangerously-skip-permissions
```

---

## 3. Configuring systemd Timer (Unattended Scheduling)

Using `systemd --user` allows running the scheduler under your user account without requiring root permissions:

```bash
# Create user systemd directory
mkdir -p ~/.config/systemd/user

# Copy unit files
cp systemd/ai-publisher.service ~/.config/systemd/user/
cp systemd/ai-publisher.timer ~/.config/systemd/user/

# Reload systemd user daemon
systemctl --user daemon-reload

# Enable and start the timer
systemctl --user enable --now ai-publisher.timer

# Check timer status and next trigger time
systemctl --user list-timers
```

To run a test job manually through systemd:
```bash
systemctl --user start ai-publisher.service
journalctl --user-unit ai-publisher.service -f
```

---

## 4. Kill Switch & Guardrails

- **Kill switch:** In `.env`, set `PUBLISHING_ENABLED=false` to halt publishing immediately.
- **Dry-run mode:** In `.env`, keep `DRY_RUN=true` to simulate all WordPress API interactions without making live network writes.
- **Daily limits:** `MAX_POSTS_PER_DAY=1` ensures the system will not exceed your defined threshold.
